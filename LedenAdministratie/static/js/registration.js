function turnondark() {
    document.getElementById('toggle').checked = true;
    localStorage.setItem('dark', 1);
    var all = document.getElementsByClassName('dark');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.add('dark-toggled');
    }
    var all = document.getElementsByClassName('semidark');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.add('semidark-toggled');
    }
    var all = document.getElementsByClassName('text');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.add('text-toggled');
    }
    var all = document.getElementsByClassName('darkborder');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.add('darkborder-toggled');
    }
    document.getElementsByClassName('background')[0].style.backgroundColor = '#030b80';
    document.getElementsByClassName('logo-upper-left')[0].style.filter = 'none';
    document.getElementsByClassName('logo-form')[0].style.filter = 'brightness(20)';
}

function turnoffdark() {
    document.getElementById('toggle').checked = false;
    localStorage.setItem('dark', 0);
    var all = document.getElementsByClassName('dark');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.remove('dark-toggled');
    }
    var all = document.getElementsByClassName('semidark');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.remove('semidark-toggled');
    }
    var all = document.getElementsByClassName('text');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.remove('text-toggled');
    }
    var all = document.getElementsByClassName('darkborder');
    for (var i = 0; i < all.length; i++) {
        all[i].classList.remove('darkborder-toggled');
    }
    document.getElementsByClassName('background')[0].style.backgroundColor = 'white';
    document.getElementsByClassName('logo-upper-left')[0].style.filter = 'invert(1)';
    document.getElementsByClassName('logo-form')[0].style.filter = 'none';

}

window.addEventListener('load', function() {
    if (localStorage.getItem('dark') == 1) {
        turnondark();
    } else {
        turnoffdark();
    }
    if (localStorage.getItem('dark') == null) {
        const darkThemeMq = window.matchMedia("(prefers-color-scheme: dark)");
        if (darkThemeMq.matches) {
            turnondark();
        }
    }
})

const checkbox = document.getElementById('toggle')

checkbox.addEventListener('change', (event) => {
    if (event.currentTarget.checked) {
        turnondark();
    } else {
        turnoffdark();
    }
})
