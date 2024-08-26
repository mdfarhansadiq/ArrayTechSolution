document.addEventListener("DOMContentLoaded", function() {
    const tabButtons = document.querySelectorAll('.tab_btn');
    const tabContents = document.querySelectorAll('.tab_content');

    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove 'active' class from all tab contents and tab buttons
            tabContents.forEach(content => content.classList.remove('active'));
            tabButtons.forEach(btn => btn.classList.remove('active'));

            // Add 'active' class to the clicked tab button
            button.classList.add('active');

            // Find the corresponding tab content and display it
            const targetContent = document.querySelector(`.tab_content.${button.classList[1]}`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });

    
});

$(document).ready(function(){
  $('.panel-collapse').on('show.bs.collapse', function () {
    $(this).siblings('.panel-heading').addClass('active');
  });

  $('.panel-collapse').on('hide.bs.collapse', function () {
    $(this).siblings('.panel-heading').removeClass('active');
  });

  $(".free_video_btn").click(function(){
    $(this).next(".free_video_modal").css({transform: "scale(1)"});
  });
  $(".video_close").click(function(){
    $(this).closest(".free_video_modal").css({transform: "scale(0)"});
  });
});

    



