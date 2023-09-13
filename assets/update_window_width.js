console.log("---------------1111111111111111111111------------------");
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    update_window_size: function() {
        return {
            width: window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth,
            height: window.innerHeight || document.documentElement.clientHeight || document.body.clientHeight
        };
    }
});

window.addEventListener('resize', function() {
    if (window.dash_clientside.update_window_size) {
        window.dash_clientside.update_window_size();
    }
});

   

