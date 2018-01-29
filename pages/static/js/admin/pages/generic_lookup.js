the_ape.page = the_ape.page || {};
the_ape.generic_lookup = the_ape.generic_lookup || {};

django.jQuery(function ($) {
    var page = the_ape.page;
    var generic_lookup = the_ape.generic_lookup;
    var lookup_selector = "input.generic-field-lookup";
    var object_id_selector = "input.generic-object-id";
    var content_type_id_selector = "input.generic-content-type-id";
    var search_results_selector = "select.search-results";

    generic_lookup.lookup_container = function (elemen) {
        if ($(".subform").length >= 1) {
            return $(elemen).parents(".subform:first");
        } else {
            return $("form");
        }
    };

    generic_lookup.bind_lookup = function () {
        $(lookup_selector).typeWatch({
            callback: function (search_string, stuff) {
                var searchbox = this;
                if (search_string.length < 3) {
                    $(searchbox).siblings(search_results_selector).remove();
                    if (search_string.length == 0) {
                        var container = generic_lookup.lookup_container(searchbox);
                        container.find(object_id_selector).val("");
                        container.find(content_type_id_selector).val("");
                    }
                } else {
                    generic_lookup.search(searchbox, search_string);
                }
            },
            wait: 500,
            higlight: false,
            captureLength: 0
        });
        $(lookup_selector).on('keyup keydown keypress', function(event) {
            if(event.keyCode == 13){
                $(event.target).data('enter', true);
            }
        });
    };

    generic_lookup.search = function (searchbox, search_string) {
        var url = $(searchbox).attr("api_url");
        $.get(url, {q: search_string}, function (data) {
            $(searchbox).siblings(search_results_selector).remove();
            $(searchbox).after(data);
            if ($(searchbox).data('enter')) {
                $(searchbox).removeData('enter');
                $(searchbox).siblings(search_results_selector).focus();
            }
        });
    };

    generic_lookup.set_option = function (option) {
        var object_id = $(option).attr("value");
        var content_type_id = $(option).attr("ct_value");
        var container = generic_lookup.lookup_container(option);
        container.find(object_id_selector).val(object_id);
        container.find(content_type_id_selector).val(content_type_id);
        generic_lookup.lookup_container(option).find(lookup_selector).val($(option).attr("full_name"));
    };

    generic_lookup.bind_lookup();
    page.widgetsList.on("addwidget", generic_lookup.bind_lookup);


    // page.form binding from the "generic_lookup" namespace
    page.form.on("change blur", search_results_selector, function (event) {
        var option = $(event.target).find("option:selected");
        generic_lookup.set_option(option);
    });
});