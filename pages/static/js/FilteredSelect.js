django.jQuery(function($) {
    function bind_filtered_select() {
        $("select.filtered-select").filter(":not(.bound)").each(function(i, select){
            select = $(select);
            var name = select.attr('name');
            var option_attic = $("<div class='attic' for='"+ name +"'></div>");
            option_attic.html(select.find('option').clone());
            select.after(option_attic);

            var lookup_id = select.attr('id') + "_lookup";
            var search_box = $("<input type='text' id='"+ lookup_id +"' for='"+ name +"'></input>");
            select.after(search_box);

            var option_count = $("<span class='option-count'></span>");
            option_count.text(select.find('option[value!=""]').length);
            search_box.after(option_count);

            search_box.keyup(function (event) {
                var search_text = search_box.val().toLowerCase();
                select.empty();

                if (search_text == '') {
                    //unhide all
                    option_attic.find('option').clone().each(function(){
                        $(this).appendTo(select)
                    });
                }
                else {
                    var new_options = option_attic.find('option').filter(function () {
                        return this.text.toLowerCase().indexOf(search_text) > -1 || $(this).val() == '';
                    }).clone();
                    select.html(new_options);

                    if (select.find('option[selected]').length == 0) {
                        select.find('option[value!=""]:first').attr("selected", "selected");
                        update_selection(event);
                    }
                }
                option_count.text(select.find('option[value!=""]').length);
            });

            function update_selection (event) {
                // keep the attic up to date with current selections
                var selected_val = select.find('option:selected').val();
                if (selected_val != "") {
                    option_attic.find('option').removeAttr('selected');
                    var new_sel = option_attic.find('[value="'+selected_val+'"]');
                    new_sel.attr('selected', 'selected');
                }
            }
            select.addClass("bound");

            select.change(update_selection);
            search_box.blur(update_selection);
        });
    }
    bind_filtered_select();

    // re-bind on dom mutation in case a new filtered select gets added
    var MutationObserver = window.MutationObserver || window.WebKitMutationObserver;
    new MutationObserver(function (mutations, observer) {
        // only re-bind if a new select.filtered-select was added
        var new_filtered_select = false;
        $(mutations).each(function (m, mutation){
            $(mutation.addedNodes).each(function(n, node) {
                if ($(node).find('select.filtered-select').length > 0) {
                    new_filtered_select = true;
                    return false;  // break
                }
            });
        });
        if (new_filtered_select) {
            bind_filtered_select();
        }
    }).observe(document, {
        childList: true,
        subtree: true,
        attributes: false
    });
});
