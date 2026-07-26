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
		this.pending_plan = null;
		this.data = [];
		this.$current_json = null;
		this.$wrap = null;
		this.counter = 0
		this.render();
	}

	render() {
		this.$wrapper = $(`
			<div class="agent-caller">
				<p class="text-muted">
					Describe what you want to do in plain English, e.g.
					<em>"Create a sales invoice for customer Jane with 3 keyboards,
					due next Friday"</em>. The local model proposes a function call
					first &mdash; nothing is created until you review it below and
					click <strong>Approve &amp; Run</strong>.
				</p>
				<textarea class="form-control agent-caller-input" rows="3"
					placeholder="What should the agent do?"></textarea>
				<div class="agent-caller-actions" style="margin-top: 10px;">
					<button class="btn btn-primary btn-sm btn-plan">
						${__('Plan')}
					</button>
				</div>
				<div class="agent-caller-result" style="margin-top: 20px; display: none;">
					<h5>${__('Proposed action')}</h5>
					<p class="text-muted small">
						${__('You can edit the JSON below before running it.')}
					</p>

					<div class="agent-caller-json-container">
						
					</div>
					<div class="agent-caller-actions" style="margin-top: 10px;">
						<button class="btn btn-success btn-sm btn-run">
							${__('Approve & Run')}
						</button>
						<button class="btn btn-default btn-sm btn-discard">
							${__('Discard')}
						</button>
					</div>
				</div>
			</div>
		`).appendTo(this.page.body);

		this.$input = this.$wrapper.find('.agent-caller-input');
		this.$result = this.$wrapper.find('.agent-caller-result');
		// this.$json = this.$wrapper.find('.agent-caller-json');
		this.$wrap = this.$wrapper
		this.$container = this.$wrapper.find('.agent-caller-json-container');

		this.$wrapper.find('.btn-plan').on('click', () => this.plan());
		this.$wrapper.find('.btn-run').on('click', () => this.run());
		this.$wrapper.find('.btn-discard').on('click', () => this.discard());
	}

	plan() {
		const query = this.$input.val();
		if (!query || !query.trim()) {
			frappe.msgprint(__('Please describe what you want to do.'));
			return;
		}

		frappe.dom.freeze(__('Asking the agent...'));
		frappe.call({
			method: 'frappe_ai.frappe_ai.page.agent_caller.agent_caller.plan',
			args: { query },
			callback: (r) => {
				frappe.dom.unfreeze();
				if (!r.message) return;
				this.pending_plan = r.message;
				this.data = [...this.data, r.message];
				this.counter = this.counter + 1
				// Create textarea element
				let $textarea = $(`
					<textarea class="form-control agent-caller-json-${this.counter}" rows="10"
						style="font-family: monospace; font-size: 12px;"></textarea>
				`);
				this.$current_json = $textarea
				// Insert JSON data
				$textarea.val(JSON.stringify(r.message, null, 2));

				// Append to container
				this.$container.append($textarea);
				// this.$json.val(
				// 	JSON.stringify({ name: r.message.name, arguments: r.message.arguments }, null, 2)
				// );

				this.$result.show();
			},
			error: () => frappe.dom.unfreeze(),
		});
	}

	run() {
		let edited;
		try {
			console.log(this.counter,  "counter");
			// json = this.$container.find(`.agent-caller-json-${this.counter}`);
			console.log(this.$current_json.val(), "json");

			edited = JSON.parse(this.$current_json.val());
			console.log(edited, "edited");
		} catch (e) {
			frappe.msgprint(__('The proposed action is not valid JSON. Fix it before running.'));
			return;
		}

		frappe.confirm(
			__('Create this {0} for {1}?', [edited.name, edited.arguments && edited.arguments.customer]),
			() => {
				frappe.dom.freeze(__('Creating...'));
				frappe.call({
					method: 'frappe_ai.frappe_ai.page.agent_caller.agent_caller.run',
					args: {
						name: edited.name,
						arguments: edited.arguments,
					},
					callback: (r) => {
						frappe.dom.unfreeze();
						if (!r.message) return;
						console.log(r.message, "first message");
						if(!r.message.created) {
							frappe.msgprint(__('The action was not created. Please check the server logs for details.'));
							// console.log(r.message, "first message");
							// frappe.confirm(
							// 	__('Create this {0}?', [r.message]),
							// 	() => {
							// 		frappe.dom.freeze(__('Creating...'));
							// 		frappe.call({
							// 			method: 'frappe_ai.frappe_ai.page.agent_caller.agent_caller.run',
							// 			args: {
							// 				name: r.message.name,
							// 				arguments: r.message.arguments,
							// 			},
							// 			callback: (r) => {
							// 				frappe.dom.unfreeze();
							// 				if (!r.message) return;
							// 				console.log(r.message, "second message");
							// 				if(!r.message.created) {
							// 					frappe.msgprint(__('The action was not created. Please check the server logs for details.'));
							// 					return;
							// 				}
							// 				frappe.show_alert({
							// 					message: __('Created {0}: {1}', [r.message.doctype, r.message]),
							// 					indicator: 'green',
							// 				});
							// 				frappe.set_route('Form', r.message.doctype, r.message.created);
							// 			},
							// 			error: () => frappe.dom.unfreeze(),
							// 		});
							// 	},
							// 	() => {
							// 		frappe.msgprint(__('Action discarded.'));
							// 	}
							// );

							this.pending_plan =  r.message ;
							this.data = [...this.data, r.message];
							this.counter = this.counter + 1
							// Create textarea element
							let $textarea = $(`
								<textarea class="form-control agent-caller-json-${this.counter}" rows="10"
									style="font-family: monospace; font-size: 12px;"></textarea>
							`);
							this.$current_json = $textarea
							// Insert JSON data
							$textarea.val(JSON.stringify(r.message, null, 2));

							// Append to container
							this.$container.append($textarea);
							// this.$json.val(
							// 	JSON.stringify({ name: r.message.name, arguments: r.message.arguments }, null, 2)
							// );
							this.$result.show();
							return;
						}
						frappe.show_alert({
							message: __('Created {0}: {1}', [r.message.doctype, r.message.created]),
							indicator: 'green',
						});
						frappe.set_route('Form', r.message.doctype, r.message.created);
					},
					error: () => frappe.dom.unfreeze(),
				});
			}
		);
	}

	discard() {
		this.pending_plan = null;
		this.$result.hide();
		this.$input.val('');
	}
};
