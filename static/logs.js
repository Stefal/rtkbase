function actionFormatter (value,row,index) {
    
    return value
}

window.operateEvents = {
    'click #log_edit': function (e, value, row, index) {
        alert('Editing: \n' + row.name)
    },
    'click #log_delete': function (e, value, row, index) {
        document.querySelector('#filename').textContent = row.name;
        $('#deleteModal').modal();
        $('#confirm-delete-button').data.row = row;
    },
    'click #log_edit': function(e, value, row, index) {
        document.querySelector('#filename').textContent = row.name;
        $('#editModal').modal();
    }
};

$('#confirm-delete-button').on("click", function (){
    socket.emit("delete log", $('#confirm-delete-button').data.row);
});

$(document).ready(function () {

    // SocketIO namespace:
    namespace = "/test";

    // initiate SocketIO connection
    socket = io.connect("http://" + document.domain + ":" + location.port + namespace);

    // say hello on connect
    socket.on("connect", function () {
        socket.emit("browser connected", {data: "I'm connected"});
    });

    console.log("log.js Asking for the available logs");
    socket.emit("get logs list");

    socket.on('disconnect', function(){
        console.log('disconnected');
    });

       // ################" TABLE ##########################"

    
    
    socket.on('available logs', function(msg){
        console.log("New log list available");
        
        var actionDownloadElt = document.createElement("a");
        actionDownloadElt.href = "#deleteModal";
        actionDownloadElt.setAttribute("title", "download");
        actionDownloadElt.setAttribute("id", "log_download")
        actionDownloadElt.classList.add("mx-1");
            var downloadImg = document.createElement("img");
            downloadImg.setAttribute("src", "../static/images/download.svg");
            downloadImg.setAttribute("alt", "download");
            downloadImg.setAttribute("title", "dOwnload");
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
            editImg.setAttribute("title", "edit");
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
            deleteImg.setAttribute("title", "dElete");
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

        

 
    
})