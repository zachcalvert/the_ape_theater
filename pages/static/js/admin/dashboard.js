/*********************************************************************
 *  Global scope
 **********************************************************************/
the_ape.dashboard = the_ape.dashboard || {};


django.jQuery(function ($) {
    /*********************************************************************
     *  cached DOM elements
     **********************************************************************/

    the_ape.dashboard.collapsible             = $( ".module_title.grp-collapse-handler:parent" );

    /*********************************************************************
     *  functions
     **********************************************************************/


    /*********************************************************************
     * Page Ready
     **********************************************************************/

    $(document).ready(function () {
        var collapseState = the_ape.cookieJar.getCookie("dashboard_state");
        if (!collapseState)
            collapseState = {};
        if ( collapseState == {} ) {
            the_ape.dashboard.collapsible.each(function() {
                collapseState[this.id] = $( this ).hasClass('grp-open');
            });
            the_ape.cookieJar.setCookie("dashboard_state", collapseState);
        }else {
            $.each(collapseState, function(key, value) {
                var myDiv = $("#"+key);
                if (!value) {
                    myDiv.toggleClass('grp-open').toggleClass('grp-closed');
                }
            });
        }

        $(document).on('click', the_ape.dashboard.collapsible, function(event){
            var my_parent = $( event.target).parent();
            var my_id = my_parent.attr('id');
            var has_class = my_parent.hasClass('grp-open');
            collapseState[my_id] = has_class ? true : false;
            the_ape.cookieJar.setCookie("dashboard_state", collapseState);
        });

    })
});