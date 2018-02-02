/*********************************************************************
 *  Global scope
 **********************************************************************/
    // Main namespace:
var the_ape = the_ape || {};
the_ape.cookieJar = the_ape.cookieJar || {};
the_ape.ajax = the_ape.ajax || {};


/*********************************************************************
 *  Global functions
 **********************************************************************/

the_ape.cookieJar.setCookie = function (cname, cvalue) {
    var d = new Date();
    d.setTime(d.getTime() + (365 * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toGMTString();
    document.cookie = cname + "=" + JSON.stringify(cvalue) + "; " + expires + "; path=/";
};

the_ape.cookieJar.getCookie = function (cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i].trim();
        if (c.indexOf(name) == 0) return JSON.parse(c.substring(name.length, c.length).trim());
    }
    return null;
};

django.jQuery(function ($) {
    /*********************************************************************
     *  cached DOM elements
     **********************************************************************/

    the_ape.ajax.loadingIndicator                 = $( "#spinner, #thinking, #saving" );


    /*********************************************************************
     *  functions
     **********************************************************************/

    function set_messages(messages, append) {
        var messagelist = $("ul.grp-messagelist");
        if (messagelist.length == 0) {
            $("#grp-content").prepend("<ul class=\"grp-messagelist\"></ul>");
            messagelist = $("ul.grp-messagelist");
        }
        if (!append) {
            messagelist.find("li").remove();
        }
        $(messages).each(function (i, message) {
            messagelist.append("<li class=\"grp-" + message.tags + "\">" + message.message + "</li>")
        });
    }

    the_ape.ajax.ajax_save = function() {

//        $("#thinking, #saving").show();
        the_ape.ajax.loadingIndicator.fadeIn('fast');
        set_messages([
            {message: "Saving...", tags: "info"}
        ]);
        $(".errorlist").remove();
        $(".grp-errors").removeClass("grp-errors");

        var form = $("form"); // TODO grabs first form; will the first form always be the right fork?
        var url = form.attr("action");
        $.post(url, form.serialize(), function (data) {
            set_messages(data['messages']);

            if (!$.isEmptyObject(data['errors'])) {
                /*
                TODO this is not where this logic belongs. If there are errors, set the message in
                TODO utils/admin.py, at about line 40 before return.
                */
                set_messages([
                    {message: "Please correct the errors below", tags: "error"}
                ]);
                for (var field in data['errors']) {
                    var field_errors = data['errors'][field];
                    var field_element = $("[name=" + field + "]");

                    field_element.parents(".grp-row").addClass("grp-errors");

                    var error_ul = $("<ul class=\"errorlist\"></ul>");
                    $(field_errors).each(function (i, error) {
                        error_ul.append("<li>" + error + "</li>");
                    });
                    field_element.after(error_ul);
                }
            }
            // The confirmation / error message is at the top, the user should be too.
            $('html,body').animate({ scrollTop: 0 }, 'fast', function() {
                the_ape.ajax.loadingIndicator.fadeOut('slow');
            });
        });
    };

    $(document).on("keydown", function (e) {
        if ((e.ctrlKey || e.metaKey) && String.fromCharCode(e.keyCode).toLocaleLowerCase() == 's') {
            e.preventDefault();
            if (window.location.pathname.match(/\/add\/?/) || window.location.pathname.match(/\/catalog\/group\/\d+\/?/)) {
                $("input[type=submit][name=_continue]").click();
            } else {
                the_ape.ajax.ajax_save();
            }
        }
    });



    /*********************************************************************
     * Page Ready
     **********************************************************************/

    $(document).ready(function () {
        // ...
    })
});