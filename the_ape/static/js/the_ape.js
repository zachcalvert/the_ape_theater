/* toggle active flags on top nav menu */
$(document).ready(function(){
    $('.navbar-collapse li').click(function() {
        $(this).siblings('li').removeClass('active');
        $(this).addClass('active');
    });
    $('.navbar-brand').click(function() {
        $('.navbar-collapse li').each(function() {
        	$(this).removeClass('active');
        });
    });
    
});