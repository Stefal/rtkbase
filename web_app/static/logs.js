function actionFormatter (value,row,index) {
    
    return value
}

window.operateEvents = {
    'click #log_delete': function (e, value, row, index) {
        document.querySelector('#filename').textContent = row.name;
        $('#deleteModal').modal();
        //put filename inside button attribute data.row to get it when the user
        // click on the confirm delete button.
        $('#confirm-delete-button').data.row = row;
    },
    'click #log_edit': function(e, value, row, index) {
        document.querySelector('#filename').textContent = row.name;
        console.log(row.format);
        if ( row.format.split(".").pop() === "ZIP") {
            $('#rinex-ign-button').removeAttr("disabled");
        }
        else {
            $('#rinex-ign-button').prop("disabled", true);;
        }
        $('#editModal').modal();
        $('#rinex-ign-button').data.row = row;
    }
};

$('#confirm-delete-button').on("click", function (){
    socket.emit("delete log", $('#confirm-delete-button').data.row);
});

$('#rinex-ign-button').on("click", function (){
    socket.emit("rinex IGN", $('#rinex-ign-button').data.row, 'ign_rinex');
    $(this).html('<span class="spinner-border spinner-border-sm"></span> Creating Rinex...');
});

$(document).ready(function () {

    // SocketIO namespace:
    namespace = "/test";

    // initiate SocketIO connection
    socket = io.connect(location.protocol + "//" + document.domain + ":" + location.port + namespace);

    // say hello on connect
    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });

    console.log("log.js Asking for the available logs");
    socket.emit("get logs list");

    socket.on('disconnect', function(){
        console.log('disconnected');
    });

    //Clean edit modal content when closing it, if there is a failed message
    $("#editModal").on('hidden.bs.modal', function(){
        socket.emit("get logs list");
        var failedTitleElt = document.getElementById("failed_title");
        if (failedTitleElt != null) {
            failedTitleElt.remove();
        };
        var failedMsgElt = document.getElementById("failed_msg");
        if (failedMsgElt != null) {
            failedMsgElt.remove();
        };
      });

       // ################" TABLE ##########################"

    socket.on('available logs', function(msg){
        console.log("New log list available");
        
        var actionDownloadElt = document.createElement("a");
        actionDownloadElt.href = "#";
        actionDownloadElt.setAttribute("title", "download");
        actionDownloadElt.setAttribute("id", "log_download")
        actionDownloadElt.classList.add("mx-1");
            var downloadImg = document.createElement("img");
            downloadImg.setAttribute("src", "../static/images/download.svg");
            downloadImg.setAttribute("alt", "download");
            downloadImg.setAttribute("title", "Download");
            downloadImg.setAttribute("width", "25");
            downloadImg.setAttribute("height", "25");
        actionDownloadElt.appendChild(downloadImg);

        var actionEditElt = document.createElement("a");
        actionEditElt.href = "#";
        actionEditElt.setAttribute("title", "edit");
        actionEditElt.setAttribute("id", "log_edit")
        actionEditElt.classList.add("mx-1");
            var editImg = document.createElement("img");
            editImg.setAttribute("src", "../static/images/pencil.svg");
            editImg.setAttribute("alt", "edit");
            editImg.setAttribute("title", "Edit");
            editImg.setAttribute("width", "25");
            editImg.setAttribute("height", "25");
        actionEditElt.appendChild(editImg);

        var actionDeleteElt = document.createElement("a");
        actionDeleteElt.href = "#";
        actionDeleteElt.setAttribute("title", "delete");
        actionDeleteElt.setAttribute("id", "log_delete");
        actionDeleteElt.setAttribute("data-toggle", "modal")
        actionDeleteElt.classList.add("mx-1");
            var deleteImg = document.createElement("img");
            deleteImg.setAttribute("src", "../static/images/trash.svg");
            deleteImg.setAttribute("alt", "delete");
            deleteImg.setAttribute("title", "Delete");
            deleteImg.setAttribute("width", "25");
            deleteImg.setAttribute("height", "25");
        actionDeleteElt.appendChild(deleteImg);

        // Adding icons for file's actions
        for (log of msg) {
            actionDownloadElt.href = "/logs/download/" + log.name
            //some download examples : https://pythonise.com/series/learning-flask/sending-files-with-flask
            log['actions'] = actionDownloadElt.outerHTML + actionEditElt.outerHTML + actionDeleteElt.outerHTML;
        }

        // Updating the table content
        $('#logtable').bootstrapTable('removeAll');
        
        $('#logtable').bootstrapTable('load', msg);
        var zz = $('#logtable').bootstrapTable('getData');
        console.log(" table data : ");
        console.log(zz);
        })

       // ################" SOCKETS ##########################"
   
        // server return the raw to rinex result
       socket.on('ign rinex ready', function(msg){
        response = JSON.parse(msg);
        console.log(response);
        if (response.result == "success") {           
            $('#rinex-ign-button').html('Create');
            location.href = "/logs/download/" + response.file;
        }
        else if (response.result == "failed") {
            $('#rinex-ign-button').html('Create');

            var failedTitleElt = document.createElement("h5");
            failedTitleElt.classList.add("text-danger");
            failedTitleElt.textContent = "Failed!";
            failedTitleElt.id = "failed_title";
            $('#editModal .modal-body').append(failedTitleElt);

            var failedElt = document.createElement("p");
            failedElt.classList.add("text-left");
            failedElt.appendChild(document.createTextNode(response.msg));
            failedElt.id = "failed_msg";
            $('#editModal .modal-body').append(failedElt);
        }
    });

})