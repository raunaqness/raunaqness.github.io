jQuery(function(){
    $("img.tileImg").cover();
});

function showProject() {
	jQuery(function(){
		$("#about").hide();
		$("#project").show();
		document.getElementById("project-label").style.fontWeight = "bold";
		document.getElementById("about-label").style.fontWeight = "normal";
		$('html, body').animate({
	    	scrollTop: 0
	    }, 300);
	});
}

function showAbout() {
	jQuery(function(){
		$("#project").hide();
		$("#about").show();
		document.getElementById("about-label").style.fontWeight = "bold";
		document.getElementById("project-label").style.fontWeight = "normal";
	});
}

showAbout();

jQuery(function(){
	if ($(window).width() >= 992) {
		var stickySidebar = $('#sidebar');

		if (stickySidebar.length > 0) { 
		  var stickyHeight = stickySidebar.height(),
		      sidebarTop = stickySidebar.offset().top;
		}

		// on scroll move the sidebar
		$(window).scroll(function () {
		  if (stickySidebar.length > 0) { 
		    var scrollTop = $(window).scrollTop();
		            
		    if (sidebarTop < scrollTop) {
		      stickySidebar.css('top', scrollTop - sidebarTop);
		    }
		    else {
		      stickySidebar.css('top', '0');
		    } 
		  }
		});

		$(window).resize(function () {
		  if (stickySidebar.length > 0) { 
		    stickyHeight = stickySidebar.height();
		  }
		});
	}

	$('.go-to-top-btn').click(function(event) {
		event.preventDefault();
	    $('html, body').animate({
	    	scrollTop: 0
	    }, 300);
    })
});