$(function () {
    $(document).on("click", "a.file-download", function (e) {
        e.preventDefault();
        var $spinner = $("#modal-spinner");
 
        $spinner.show();
 
        $.fileDownload($(this).prop('href'), {
            successCallback: function (url) {
 
                $spinner.hide();
            },
            failCallback: function (responseHtml, url) {
 
                $spinner.hide();
                // $("#error-modal").dialog({ modal: true });
            }
        });
        return false; //this is critical to stop the click event which will trigger a normal file download!
    });
});


// example
// $(function () {
//     $(document).on("click", "a.fileDownloadCustomRichExperience", function (e) {
//         e.preventDefault();
//         var $preparingFileModal = $("#preparing-file-modal");
 
//         $preparingFileModal.dialog({ modal: true });
 
//         $.fileDownload($(this).prop('href'), {
//             successCallback: function (url) {
 
//                 $preparingFileModal.dialog('close');
//             },
//             failCallback: function (responseHtml, url) {
 
//                 $preparingFileModal.dialog('close');
//                 $("#error-modal").dialog({ modal: true });
//             }
//         });
//         return false; //this is critical to stop the click event which will trigger a normal file download!
//     });
// });
