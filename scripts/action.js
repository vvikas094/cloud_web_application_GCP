$(document).ready(function() {

    var radio = $('input[name="choice-image"]'),
        defaultAction = $("#form").attr('action');
    radio.change(function(e) {
        $('#imageURL').val("");
        $('#imageFile').val("");
        if (this.value === 'image-url') {
            $("#form").attr('action', '/imagehandler');
        } else {
            $.ajax({
                url: '/createUploadHandler',
                type: 'get',
                success: function(data) {
                    $("#form").attr('action', data);
                }
            });

        }
    });
    $('#form').submit(function() {
            var imageURLContent = $('#imageURL').val().length;
            var imageFileContent = $('#imageFile').val().length;
            if (imageURLContent > 0 || imageFileContent > 0) {
                if ($("#form").attr('action') === 'image-file') {
                    $("#form").attr('action', '');

                var getRequest = $.ajax({
                        url: '/createUploadHandler',
                        type: 'get',
                        success: function(data) {
                            $("#form").attr('action', data);
                        }
                    });
                getRequest.done(function() {
                    $("div#runningindicator").show();
                    var request = $.ajax({
                        url: $('#form').attr('action'),
                        type: 'post',
                        target: $('#form').attr('target'),
                        success: function(data) {

                        },
                        error: function(msg) {}
                    });
                    request.done(function(msg) {

                        $('#imageURL').val("");
                        $('#imageFile').val("");
                    });
                })
            } else {
            	$("div#runningindicator").show();
            }

            return true;
        } else {
            alert('Image URL/File Missing');
            return false;
        }
    });

$('#otpFrame').on('load', function() {
    $('#imageURL').val("");
    $('#imageFile').val("");
    $("div#runningindicator").hide();
});
});

function showValue(identity, newValue) {
    document.getElementById(identity).innerHTML = newValue;
}