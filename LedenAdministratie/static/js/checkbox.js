
$(document).ready(function() {
    var $selectAll = $('#selectAll'); // main checkbox inside table thead
    var $table = $('.table'); // table selector
    var $tdCheckbox = $table.find('tbody input:checkbox'); // checboxes inside table body
    var $tdCheckboxChecked = []; // checked checbox arr

    $tdCheckbox.each(function() {
        $(this).prop('checked', true);
    });

    //Select or deselect all checkboxes on main checkbox change
    $selectAll.on('click', function () {
        $tdCheckbox.prop('checked', this.checked);
    });

    //Switch main checkbox state to checked when all checkboxes inside tbody tag is checked
    $tdCheckbox.on('change', function(){
        $tdCheckboxChecked = $table.find('tbody input:checkbox:checked');//Collect all checked checkboxes from tbody tag
        $selectAll.prop('checked', ($tdCheckboxChecked.length == $tdCheckbox.length));
    })
});

$('#id_invoice_types').change(function() {
    $('#mainform').submit();
});
