

$(document).ready(function() {
    $("#searchbar").val("");
    $("#searchbar").keyup(function() {
        var filter, tr, td, i, txtValue;
        filter = $("#searchbar").val().toUpperCase();
        tr = $("table:first").find("tr");

        // Loop through all table rows, and hide those who don't match the search query
        for (i = 0; i < tr.length; i++) {
            td = tr[i].getElementsByTagName("td")[0];
            if (td) {
                txtValue = td.textContent || td.innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    tr[i].style.display = "";
                } else {
                    tr[i].style.display = "none";
                }
            }
        }
    });

    $("table:first > thead > tr").children('th').each(function() {
        if ($(this)[0].innerText != '') {
            $(this).click(tableSort);
            $(this).css('cursor', 'ns-resize');
        }
    })
});


function fixForSorting(text) {

    text = text.replace(',', '.');
    number = Number(text);
    if (isNaN(number)) {
        var re = /(\d\d)-(\d\d)-(\d\d\d\d)/;
        match = text.match(text);
        if (match) {
            text = text.replace(re, "$3-$2-$1");
        }
        return text;
    } else {
        return number;
    }
}

function tableSort(column) {
    column.target.order = !column.target.order;
    let rows = $('table:first > tbody').children('tr').get();
    rows.sort(function(a, b) {

        text1 = a.children[column.target.cellIndex].innerText.toLowerCase();
        text2 = b.children[column.target.cellIndex].innerText.toLowerCase();

        text1 = fixForSorting(text1);
        text2 = fixForSorting(text2);

        if (column.target.order) {
            return text1 > text2;
        } else {
            return text2 > text1;
        }
    });
    for (var i = 0; i < rows.length; i++) {
        $('table:first > tbody').append(rows[i]);
    }
}
