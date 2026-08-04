frappe.pages['agent-caller'].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Agent Caller',
		single_column: true,
	});

	new frappe_ai.AgentCaller(page);
};

frappe.provide('frappe_ai');

frappe_ai.AgentCaller = class AgentCaller {
	constructor(page) {
		this.page = page;
		this.step_count = 0;
		this.auto_approve = false;
		this.render();
		this.bind_realtime();
	}

	new_request_id() {
		return 'req-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 8);
	}

	render() {
		this.$wrapper = $(`
			<div class="agent-caller">
				<p class="text-muted">
					Describe what you want to do in plain English, e.g.
					<em>"Create a sales invoice for customer Jane with 3 keyboards,
					due next Friday"</em>. The local model proposes a function call
					first &mdash; nothing is created until you review it and click
					<strong>Approve &amp; Run</strong> (unless auto-approve is on
					below). If a step needs something that doesn't exist yet (like a
					new Customer), the agent proposes that as a follow-up step
					automatically.
				</p>
				<textarea class="form-control agent-caller-input" rows="3"
					placeholder="What should the agent do?"></textarea>
				<div class="agent-caller-actions" style="margin-top: 10px; display: flex; align-items: center; gap: 16px;">
					<button class="btn btn-primary btn-sm btn-plan">${__('Plan')}</button>
					<label style="display: flex; align-items: center; gap: 6px; margin: 0; font-weight: normal;">
						<input type="checkbox" class="agent-caller-auto-approve">
						${__('Auto-approve all steps (run through to completion without asking)')}
					</label>
				</div>

				<div class="agent-caller-activity" style="margin-top: 16px;">
					<h6 style="margin-bottom: 6px;">${__('Activity')}</h6>
					<div class="agent-caller-activity-log" style="
						max-height: 160px; overflow-y: auto; font-family: monospace; font-size: 12px;
						background: var(--bg-color); border: 1px solid var(--border-color);
						border-radius: var(--border-radius); padding: 8px;
					">
						<div class="text-muted">${__('Nothing running yet.')}</div>
					</div>
				</div>

				<div class="agent-caller-steps" style="margin-top: 20px;"></div>
			</div>
		`).appendTo(this.page.body);

		this.$input = this.$wrapper.find('.agent-caller-input');
		this.$steps = this.$wrapper.find('.agent-caller-steps');
		this.$activity_log = this.$wrapper.find('.agent-caller-activity-log');
		this.$auto_approve = this.$wrapper.find('.agent-caller-auto-approve');

		this.$auto_approve.on('change', () => {
			this.auto_approve = this.$auto_approve.is(':checked');
		});

		this.$wrapper.find('.btn-plan').on('click', () => this.plan());
	}

	/** Subscribe once to the realtime progress channel the backend publishes
	 * to (see agent_caller.py: _progress / frappe.publish_realtime). Every
	 * plan()/run() call tags its events with a request_id we generate, so we
	 * can log them without them getting mixed up between concurrent calls. */
	bind_realtime() {
		frappe.realtime.on('agent_caller_progress', (data) => {
			this.log_activity(data.text);
		});
	}

	log_activity(text) {
		if (this.$activity_log.find('.text-muted').length) {
			this.$activity_log.empty();
		}
		const time = new Date().toLocaleTimeString();
		this.$activity_log.append(
			$('<div>').text(`[${time}] ${text}`)
		);
		this.$activity_log.scrollTop(this.$activity_log[0].scrollHeight);
	}

	plan() {
		const query = this.$input.val();
		if (!query || !query.trim()) {
			frappe.msgprint(__('Please describe what you want to do.'));
			return;
		}

		const request_id = this.new_request_id();
		frappe.dom.freeze(__('Asking the agent...'));
		frappe.call({
			method: 'frappe_ai.agent_caller.plan',
			args: { query, request_id },
			callback: (r) => {
				frappe.dom.unfreeze();
				if (!r.message) return;
				this.show_step(r.message, null);
			},
			error: () => frappe.dom.unfreeze(),
		});
	}

	/**
	 * Render one reviewable step. `then`, if given, is queued as the next
	 * step once this one succeeds. In auto-approve mode, the step still
	 * renders (so there's a visible record of what ran) but is executed
	 * immediately instead of waiting for a click.
	 */
	show_step(proposal, note, then) {
		this.step_count += 1;
		const step_id = this.step_count;

		const $step = $(`
			<div class="agent-caller-step" style="margin-bottom: 20px; padding: 10px; border: 1px solid var(--border-color); border-radius: var(--border-radius);">
				${note ? `<p class="text-muted small">${frappe.utils.escape_html(note)}</p>` : ''}
				<h6>${__('Step')} ${step_id}: ${__('Proposed action')}</h6>
				<textarea class="form-control agent-caller-json" rows="10"
					style="font-family: monospace; font-size: 12px;"></textarea>
				<div class="agent-caller-actions" style="margin-top: 10px;">
					<button class="btn btn-success btn-sm btn-run">${__('Approve & Run')}</button>
					<button class="btn btn-default btn-sm btn-discard">${__('Discard')}</button>
				</div>
				<div class="agent-caller-step-result" style="margin-top: 10px;"></div>
			</div>
		`).appendTo(this.$steps);

		const $json = $step.find('.agent-caller-json');
		const $result = $step.find('.agent-caller-step-result');
		$json.val(JSON.stringify({ name: proposal.name, arguments: proposal.arguments }, null, 2));

		const try_run = () => {
			let edited;
			try {
				edited = JSON.parse($json.val());
			} catch (e) {
				frappe.msgprint(__('This step is not valid JSON. Fix it before running.'));
				return;
			}
			this.run_step(edited, $step, $result, then);
		};

		$step.find('.btn-run').on('click', try_run);
		$step.find('.btn-discard').on('click', () => $step.remove());

		if (this.auto_approve) {
			$step.find('.btn-run, .btn-discard').prop('disabled', true);
			$result.html(`<div class="text-muted">${__('Auto-approve is on -- running now...')}</div>`);
			try_run();
		}
	}

	run_step(edited, $step, $result, then) {
		const do_run = () => {
			const request_id = this.new_request_id();
			frappe.dom.freeze(__('Running...'));
			frappe.call({
				method: 'frappe_ai.agent_caller.run',
				args: { name: edited.name, arguments: edited.arguments, request_id },
				callback: (r) => {
					frappe.dom.unfreeze();
					if (!r.message) return;
					this.handle_result(r.message, $step, $result, then);
				},
				error: () => frappe.dom.unfreeze(),
			});
		};

		if (this.auto_approve) {
			do_run();
			return;
		}

		frappe.confirm(
			__('Run {0} for {1}?', [edited.name, (edited.arguments && edited.arguments.customer) || '']),
			do_run
		);
	}

	handle_result(result, $step, $result, then) {
		if (result.created) {
			$result.html(`
				<div class="text-success">
					${__('Created')} ${frappe.utils.escape_html(result.doctype)}:
					<a href="/app/${frappe.router.slug(result.doctype)}/${encodeURIComponent(result.name)}">
						${frappe.utils.escape_html(result.name)}
					</a>
				</div>
			`);
			frappe.show_alert({
				message: __('Created {0}: {1}', [result.doctype, result.name]),
				indicator: 'green',
			});
			$step.find('.btn-run, .btn-discard').prop('disabled', true);

			if (then) {
				this.show_step(
					then,
					__('Retrying the original request now that the step above has completed:')
				);
			}
			return;
		}

		$result.html(`
			<div class="text-danger">${frappe.utils.escape_html(result.error || __('Action was not created.'))}</div>
		`);

		if (result.next_action) {
			const note = result.then
				? __('Follow-up step needed before the original request can succeed:')
				: __('Follow-up step needed:');
			this.show_step(result.next_action, note, result.then);
		}
	}
};
