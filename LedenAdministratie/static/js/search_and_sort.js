

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
        $(this).click(tableSort);
        $(this).css('cursor', 'ns-resize');
    })
});


function tableSort(column) {
    var rows = $('table:first > tbody').children('tr').get();
    rows.sort(function(a, b) {

        text1 = a.children[column.target.cellIndex].innerText.toLowerCase();
        text2 = b.children[column.target.cellIndex].innerText.toLowerCase();

        return text1 > text2;
    });
    for (var i = 0; i < rows.length; i++) {
        $('table:first > tbody').append(rows[i]);
    }
}
