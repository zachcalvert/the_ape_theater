/*********************************************************************
 *  Global scope
 **********************************************************************/
the_ape.page              = the_ape.page || {};
the_ape.page.change       = the_ape.page.change || {};
the_ape.page.widget_link  = the_ape.page.widget_link || {};

django.jQuery(function ($) {
    /**
     * page is our App, change and widget_link are separated for differences of functional intent
     */
    var page        = the_ape.page;
    var change      = the_ape.page.change;
    var widget_link = the_ape.page.widget_link;


    /*********************************************************************
     *  cached DOM elements
     **********************************************************************/

    page.widgetCountField         = $( "#id_widget_form_count" );
    page.form                     = $( "form" );
    page.dhWidgetFormAdd          = $("a.dh-widget-form-add");
    page.addExistingOptions       = $("#add-existing-options");
    page.dhExistingWidget         = $(".dh-existing-widget");
    page.dhUndoDelete             = $(".dh-undo-delete");
    page.widgetsList              = $("#widgets-list");
    page.uiSortable               = $(".ui-sortable");
    page.widgetsListuiSortable    = $("#widgets-list.ui-sortable");
    page.addExistingWidget        = $("a.add-existing-widget");
    page.inputWidgetId            = $("input.widget_id");
    page.widgetNameAndPage        = $("input.widget_name, input.widget_page");
    page.idSlug                   = $("#id_slug");

    /*********************************************************************
     *  functions
     **********************************************************************/


    change.update_management_form = function(formset) {
        var formset_prefix = formset.attr("prefix");
        var total_forms = $("#id_"+formset_prefix+"-TOTAL_FORMS");
        total_forms.attr("value", formset.find("tr.item-form").length);
    };

    change.update_widgets_order = function() {
        $(".widget-form").each(function(i, form) {
            $(form).find('.widget-sort-order').attr("value", i);
        });
    };

     change.update_widget_formset_order = function(formset) {
        formset.find(".widget-item-sort-order").each(function (i, input) {
            $(input).val(i);
        });
    };

    change.bind_formset_sorting = function() {
        $(".formset-table tbody").each(function (i, tbody) {
            $(tbody).sortable({
                axis: "y",
                handle: ".grp-drag-handler",
                helper: function (e, ui) {
                    ui.children().each(function () {
                        $(this).width($(this).width());
                    });
                    return ui;
                },
                stop: function (event, ui) {
                    change.update_widget_formset_order($(this).parents('.formset-table'));
                }
            });
        });
    };

    change.increment_form_count = function(step) {
        if (typeof step === 'undefined') {
            step = 1
        }
        var widget_count = parseInt(page.widgetCountField.attr("value"));
        page.widgetCountField.attr("value", widget_count + step);
    };

    change.add_widget_form = function(url, get_params, open) {
        change.increment_form_count();
        $.get(url, get_params, function (data) {
            data = data.replace('widget-form', 'widget-form new');
            if (open) {
                data = data.replace('grp-closed', 'grp-open');
            }
            var widgets_list = $("#widgets-list");
            widgets_list.append(data);
            change.update_widgets_order();
            change.bind_formset_sorting();
            widgets_list.trigger("addwidget");
        }).fail(function() {
            change.increment_form_count(-1);
        });
    };

    change.add_existing = function(event) {
        event.preventDefault();
        var tab = $(event.target).parents(".add-widget-tab");
        var url = tab.find("a.add-existing-widget").attr('href');
        var widget_id = tab.find("input,select").filter(".widget_id").val();
        if (widget_id) {
            var widget_count = parseInt(page.widgetCountField.attr("value"));
            change.add_widget_form(url, {widget_id: widget_id, prefix: widget_count, add_existing: true});
        }
        $( "select.widget_id option,optgroup" ).remove();
        $( "select.widget_id" ).attr("size", 0);
    };

    widget_link.search_for_link = function(searchbox, search_string) {
        var url = $(searchbox).attr("api_url");
        $.get(url, {q: search_string}, function(data) {
            $(searchbox).siblings(".link-search-results").remove();
            $(searchbox).after(data);
        });
    };

    widget_link.watch_link_lookup = function(){
        // TODO put this back to $("input").find(".page-link-lookup")
        $("input.page-link-lookup").typeWatch({
            callback: function(search_string) {
                var searchbox = this;
                if (search_string.length < 3) {
                    $(searchbox).siblings(".link-search-results").remove();
                    if (search_string.length == 0) {
                        var container = widget_link.lookup_container(searchbox);
                        container.find("input.page-link-id").val("");
                        container.find("input.page-link-type").val("");
                    }
                } else {
                    widget_link.search_for_link(searchbox, search_string);
                }
            },
            wait: 500,
            higlight: false,
            captureLength: 0
        });
    };

    widget_link.lookup_container = function(link_option) {
        if ($(".subform").length >=1) {
            return $(link_option).parents(".subform:first");
        } else {
            return $("form");
        }
    };

    widget_link.set_link_option = function(option) {
        var link_id = $(option).attr("value");
        var link_type = $(option).attr("ct_value");
        var container = widget_link.lookup_container(option);
        container.find("input.page-link-id").val(link_id);
        container.find("input.page-link-type").val(link_type);
    };

    widget_link.choose_option = function(option) {
        widget_link.set_link_option(option);
        widget_link.lookup_container(option).find("input.page-link-lookup").val($(option).attr("fullname"));
        $(option).parents("select.link-search-results").remove();
    };

    /*********************************************************************
     * Document Ready Function
     * // Load functions and set events after the DOM has fully loaded,
     * // not during
     **********************************************************************/

    $(document).ready(function () {

        /**
         * Initial Function calls
         */
        change.update_widgets_order(); //initial page load

        widget_link.watch_link_lookup();

        /**
         * Initial Bindings
         */
        page.dhWidgetFormAdd.click(function (event) {
            event.preventDefault();

            var url = $(event.target).attr('href');
            var widget_count = parseInt(page.widgetCountField.attr("value"));
            change.add_widget_form(url, {prefix: widget_count}, true);
        });

        page.addExistingOptions.tabs().hide();

        page.dhExistingWidget.click(function (event) {
            event.preventDefault();
            page.addExistingOptions.toggle();
        });

        page.dhUndoDelete.click(function (event) {
            var deleted = $(".widget-form.deleted, .item-form.deleted");
            deleted.show();
            deleted.removeClass("deleted");
            deleted.find(".widget-delete").attr('value', false);
            deleted.find(".widget-item-delete").attr('value', false);
            $(".dh-undo-delete").hide();
        });
        page.dhUndoDelete.hide();

        page.widgetsListuiSortable.sortable({
            axis: "y",
            handle: ".widget.grp-drag-handler",
            helper: function (e, ui) {
                ui = $(ui).clone();
                ui.removeClass('grp-open');
                ui.addClass('grp-closed');
                return ui;
            },
            start: function (event, ui) {
                ui.placeholder.height(ui.helper.find(".grp-collapse-handler").height());
            },
            stop: function (event, ui) {
                change.update_widgets_order();
            }
        });

        change.bind_formset_sorting();

        page.addExistingWidget.click(change.add_existing);

        page.inputWidgetId.keypress(function (event) {
            var code = event.keyCode || event.which;
            if (code == 13) {
                change.add_existing(event);
            }
        });

        page.widgetNameAndPage.typeWatch({
            callback: function (search_string) {
                var searchbox = $(this);
                var result_select = searchbox.siblings('select.widget_id');
                if (search_string == "") {
                    result_select.find("option, optgroup").remove();
                    result_select.attr("size", 1);
                    return;
                } else if (search_string == "*") {
                    search_string = "";
                }

                var url = searchbox.data('api-url');
                $.get(url, {q: search_string}, function(data) {
                    result_select.replaceWith(data);
                });
            },
            wait: 250,
            higlight: false,
            captureLength: 0
        });

        // show warnings for the page that will be replaced if this slug is chosen
        page.idSlug.change(function (event) {
            $(event.target).next(".slug-warning").remove();
            var slug = $(event.target).find("option:selected").val();
            if (slug != "") {
                var warning = $("#used-slugs").find('.slug-warning').find('.'+slug);
                console.log(warning);
                if (warning.length > 0) {
                    $(event.target).after(warning.clone());
                }
            }
        });

        /**
         * This is annoying to read, but "chaining" is apparently faster according to several sources on
         * the interwebs, including:
         * http://24ways.org/2011/your-jquery-now-with-less-suck/
         * and
         * http://tobiasahlin.com/blog/quick-guide-chaining-in-jquery/
         *
         * I don't think it's quite as easy to read, so if your heart really desires to unchain it,
         * you have my blessing.
         */
        // page.form binding from the "change" namespace
        page.form.on("keypress", function (e) {
            if (e.keyCode == 13 && !$(e.target).is("textarea")) { // enter
                e.preventDefault();
                return false;
            }
        }).on("click", "a.dh-formset-add", function (event) {
            event.preventDefault();

            var formset = $(event.target).parents("table.formset-table");
            var new_form = formset.find("tr.empty-form").clone();
            var new_index = formset.find("tr.item-form").length;
            new_form.removeClass('empty-form');
            new_form.addClass('item-form new');
            formset.find("tr.empty-form").before(new_form);

            //update field names
            new_form.find("[name]").each(function(i, input){
                var id = $(input).attr("id");
                id = id.replace("__prefix__", new_index);
                $(input).attr("id", id);

                var name = $(input).attr("name");
                name = name.replace("__prefix__", new_index);
                $(input).attr("name", name);

                change.update_management_form(formset);
                change.update_widget_formset_order(formset);
            });
            $("#widgets-list").trigger("addwidget");
        }).on("click", ".widget-form.new .grp-collapse-handler", function (event) {
            event.preventDefault();
            var collapser = $(event.target).parents('.grp-collapse');
            if (collapser.hasClass('grp-open')) {
                collapser.removeClass('grp-open');
                collapser.addClass('grp-closed');
            } else if (collapser.hasClass('grp-closed')) {
                collapser.removeClass('grp-closed');
                collapser.addClass('grp-open');
            }
        }).on("click", ".widget-form .widget.grp-remove-handler", function (event) {
            event.preventDefault();
            var widget = $(event.target).parents(".widget-form");
            widget.find(".widget-delete").attr('value', true);
            widget.addClass("deleted");
            widget.hide();
            $(".dh-undo-delete").show();
        }).on("click", ".formset-table .grp-remove-handler", function (event) {
            event.preventDefault();
            var item = $(event.target).parents("tr.item-form");
            item.find(".widget-item-delete").attr('value', true);
            item.addClass("deleted");
            item.hide();
            $(".dh-undo-delete").show();
        }).on("dblclick", "select.widget_id option", change.add_existing);

        page.widgetsList.on("addwidget", widget_link.watch_link_lookup);
        page.widgetsList.on("addwidget", grappelli.initDateAndTimePicker);

        // page.form binding from the "widget_link" namespace
        page.form.on("keypress", "input.page-link-lookup", function (event) {
            if (event.keyCode == 13) { //enter
                event.preventDefault();
                widget_link.search_for_link(event.target, $(event.target).val());
                if (search_string.length == 0) {
                    $(searchbox).siblings(".link-search-results").remove();
                } else {
                    widget_link.search_for_link(event.target, $(event.target).val());
                }
            }
        }).on("keyup", "input.page-link-lookup", function (event) {
            if (event.keyCode == 40) { //down arrow
                var container = widget_link.lookup_container(event.target);
                container.find("select.link-search-results").focus();
            }
        }).on("click change", "select.link-search-results option", function(event) {
            widget_link.set_link_option(event.target);
        }).on("dblclick", "select.link-search-results option", function(event) {
            widget_link.choose_option(event.target);
        }).on("keypress", "select.link-search-results", function(event) {
            if (event.keyCode == 13) {
                event.preventDefault();
                widget_link.choose_option($(event.target).find("option:selected"));
            }
        });


    });  // document.ready
}); // django.jquery
