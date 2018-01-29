var the_ape = the_ape || {};
the_ape.fk_autocomplete = the_ape.fk_autocomplete || {};

django.jQuery(function ($) {
    the_ape.fk_autocomplete.autocomplete_lookup = $(".autocomplete-lookup");

    the_ape.fk_autocomplete.bind_autocomplete = function() {
        the_ape.fk_autocomplete.autocomplete_lookup.typeWatch({
            callback: function(search_string) {
                var searchbox = this;
                var choices = $(searchbox).siblings("select.autocomplete-select");

                if (search_string == "") {
                    // empty the search
                    choices.find("option[value!=]").remove();
                }
                else {
                    if (search_string == "*") {
                        search_string = ""; // look for everything
                    }
                    var url = $(searchbox).data("api_url");
                    var get_params = {
                        term: search_string,
                        app_label: $(searchbox).data("app_label"),
                        model_name: $(searchbox).data("model_name")
                    };

                    $.get(url, get_params, function (data) {
                        choices.find("option[value!=]").remove();
                        $(data).each(function (i, option) {
                            choices.append("<option value='"+option.value+"'>"+option.label+"</option>");
                        });
                        choices.find("option[value!=]:first").attr('selected', 'selected');
                    }, "json");
                }
            },
            wait: 500,
            highlight: false,
            captureLength: 0
        });
    };

    the_ape.fk_autocomplete.bind_autocomplete();

    // re-bind on dom mutation in case a new autocomplete form is added (typeWatch doesn't support dynamic binding)
    var MutationObserver = window.MutationObserver || window.WebKitMutationObserver;
    new MutationObserver(function (mutations, observer) {
        the_ape.fk_autocomplete.bind_autocomplete();
    }).observe(document, {
        childList: true,
        subtree: true,
        attributes: false
    });
});