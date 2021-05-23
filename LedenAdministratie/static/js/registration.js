function turnondark() {
    if (toggle = document.getElementById('toggle')) {
        toggle.checked = true;
    }
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
    Array.from(document.getElementsByClassName('background')).forEach(element => element.style.backgroundColor = '#030b80');
    Array.from(document.getElementsByClassName('logo-upper-left')).forEach(element => element.style.filter = 'none' );
    Array.from(document.getElementsByClassName('logo-form')).forEach(element => element.style.filter = 'brightness(20)');
}

function turnoffdark() {
    if (toggle = document.getElementById('toggle')) {
        toggle.checked = false;
    }
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
    Array.from(document.getElementsByClassName('background')).forEach(element => element.style.backgroundColor = 'white');
    Array.from(document.getElementsByClassName('logo-upper-left')).forEach(element => element.style.filter = 'invert(1)');
    Array.from(document.getElementsByClassName('logo-form')).forEach(element => element.style.filter = 'none');
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
if (checkbox) {
    checkbox.addEventListener('change', (event) => {
        if (event.currentTarget.checked) {
            turnondark();
        } else {
            turnoffdark();
        }
    })
}
