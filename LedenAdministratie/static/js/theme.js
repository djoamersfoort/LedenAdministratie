let darkTheme = null;

// function to update the localstorage
function toggleTheme() {
    darkTheme = !darkTheme;
    localStorage.setItem("darkTheme", darkTheme);
}

// function to update the user interface
function updateUI() {
    $("body").removeClass("light");
    $(".theme-toggle").html(darkTheme ? "&#127769;" : "&#128262;");
    
    if(!darkTheme) {
        $("body").addClass("light");
    }
}

// on document load
$(document).ready(function() {
    // get user preference from colorscheme if applicable
    const preference = window.matchMedia("(prefers-color-scheme: dark)").matches;

    // update to colorscheme if no preference is set
    if(!localStorage.getItem("darkTheme")) {
        localStorage.setItem("darkTheme", preference);
    }

    darkTheme = localStorage.getItem("darkTheme") === "true";

    // update user-interface
    updateUI();

    // add event listener to switch
    $(".theme-toggle").click(function() {
        $(this).blur();
        
        // animation class
        $("body").addClass("animate");
        setTimeout(() => {
            $("body").removeClass("animate");
        }, 300);

        // toggle theme
        toggleTheme();
        updateUI();
    });
});