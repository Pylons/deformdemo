swap_stylesheets = function(node){
    $('#new_css').remove();
    var stylesheet = $('.swap_stylesheets')[0].value;
    if (stylesheet != 'off'){
        var css_link = $('<link />',{
                type:'text/css',
                id:'new_css',
                rel:"stylesheet",
                href:stylesheets[Number(stylesheet)]
                }
        );
        css_link.appendTo('head');
    }
}

$(document).ready(function () {
    $('.swap_stylesheets').change(swap_stylesheets);
    swap_stylesheets();
});