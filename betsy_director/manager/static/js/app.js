$(document).ready(function(){
    var NAMESPACE = '/events';

    // the socket.io documentation recommends sending an explicit package upon connection
    // this is specially important when using the global namespace
    var socket = io.connect('http://' + document.domain + ':' + location.port + NAMESPACE);

    $(window).bind('beforeunload', function() {
        socket.disconnect();
    });

    //socket.emit('my event', {data: 'I\'m connected!'});
    socket.on('connect', function() {
        console.log("socketio connect");
    });
    
    socket.on('reconnect', function() {
        console.log("socketio reconnect");
    });

    socket.on('disconnect', function() {
        console.log("socketio disconnect");
    });

    socket.on('clients', function(msg) {
        console.log("client msg:", msg);
        if (msg.num_clients) {
            $("#num_clients").text(msg.num_clients);
        }
        //socket.emit('my event', {data: 'I\'m connected!'});
    });

    $.getJSON('/gridmap').done(function(data) {
        if (data.display_size) {
            var x = data.display_size[0];
            var y = data.display_size[1];
            $("#display_size").text(x + "x" + y);
        }
    }).fail(function(jqXHR, textStatus, error) {
        console.log("failed to retrieve gridmap");
    });
});

