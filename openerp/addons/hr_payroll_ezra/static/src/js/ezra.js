 openerp.hr_payroll_ezra = function (instance) {
    instance.web.list.columns.add('field.grosspaycolor', 'instance.hr_payroll_ezra.grosspaycolor');
    instance.hr_payroll_ezra.grosspaycolor = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            res = this._super.apply(this, arguments);
            var amount = parseFloat(res);
            //return "<font color='#0000CD'>"+amount.toFixed(2)+"</font>";
            return "<font color='#8B0000'>"+amount.toFixed(2)+"</font>";
            //return amount.toFixed(2);
        }
    });

    instance.web.list.columns.add('field.deduction', 'instance.hr_payroll_ezra.deduction');
    instance.hr_payroll_ezra.deduction = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            res = this._super.apply(this, arguments);
            var amount = parseFloat(res);
            return "<font color='#8B0000'>"+amount.toFixed(2)+"</font>";
            //return amount.toFixed(2);
        }
    });

    instance.web.ActionManager = instance.web.ActionManager.extend({

        ir_actions_act_close_wizard_and_reload_view: function (action, options) {
            if (!this.dialog) {
                options.on_close();
            }
            this.dialog_stop();
            //this.inner_widget.views[this.inner_widget.active_view].controller.reload();
            this.inner_widget.active_view.controller.reload();
            return $.when();
        },
    });

};
