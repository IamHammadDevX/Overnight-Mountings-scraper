// Toggle between showing and hiding the sidebar when clicking the menu icon
let navmainexpanded = document.getElementById("navmainexpanded");

function mobilemenutoggle() {
	document.getElementById("mobilenavbtn").classList.toggle("mobilemenuposition");
	document.getElementById("topnav").classList.toggle("mobilemenuposition");
	document.getElementById("mobilenavBG").classList.toggle("mobilemenuposition");
}

//Create custom alerts with text and a mood of 'good', 'bad', or other:
function sysalert(text, mood) {
	let holder = document.getElementById("systemmessages");
	
	let message = document.createElement("div");
		message.setAttribute("onclick", "dismiss(this)");
		message.setAttribute("class", "sysmessage " + mood);
		message.setAttribute("role", "alert");
		message.innerHTML = "<p>" + text + "</p>";
	holder.appendChild(message);
	
	setTimeout(() => {
		message.style.top = "20px";
		message.style.opacity = "1";
	}, 100);
	
	text = text.replaceAll("<br>", " ");
	//Dynamic wait times for despawning the alert: Divides word count by average WPM times seconds plus 2 extra seconds:
	let delay = text.split(" ").length / 200 * 60 + 2;
	setTimeout(() => {dismiss(message)}, delay * 1000);
	
	if (mood.startsWith("good")) { console.log("%c" + text, "color: #009E28;"); }
	else if (mood.startsWith("bad")) { console.error(text); }
	else if (mood == "aria") { console.log(text); }
	else { console.warn(text); }
}
//For when an alert message is clicked:
function dismiss(message) {
	try {
		message.removeAttribute("style");
		setTimeout(function hidemessage(){message.remove();}, 300);
	}
	catch {}
}

//Opens the main navigation menu:
function setnavcontent(whichone) {
	headerpreview.parentElement.style.backgroundImage = "unset";
	//Clear the image after fading (this makes it fade from emptiness when the function is called again):
	headerpreview.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E";
	
	let nmrElems = document.querySelectorAll(".nmrcategory");
	
	//For every element minus the logo...
	for (i=0; i < nmrElems.length; i++) {
		navmainexpanded.children[i].classList.remove("nmechosen");
		nmrElems[i].classList.remove("nmrchosen");
		if (whichone) { navmainexpanded.children[whichone].children[0].classList.remove("visibleheaderlisting"); }
	}
	
	if (whichone !== undefined) { //'!== undefined' is needed to account for 0.
		navmainexpanded.children[whichone].classList.add("nmechosen");
		nmrElems[whichone].classList.add("nmrchosen");
		navmainexpanded.children[whichone].children[0].classList.add("visibleheaderlisting");
	}
		//Defaults sub-hover to the top product listing:
		//setnavproducts(0);
}

function refocus(element) { document.querySelector("[name='" + element + "']").focus(); }

function copytoclipboard(copythat) {
	navigator.clipboard.writeText(copythat).then(
		() => { sysalert("Copied to clipboard.", "good"); },
		() => { sysalert("Error copying to clipboard.", "bad"); },
	);
}

openwindows = [];

// Disabled until all new elements get dark mode colors:
/* LIGHT/DARK MODE TOGGLING: */
/*const toggleSwitch = document.querySelector('#themecheckbox');
const currentTheme = localStorage.getItem('theme');

if (currentTheme) {
	document.documentElement.setAttribute('data-theme', currentTheme);

	if (currentTheme === 'dark') {
		try { toggleSwitch.checked = true; }
		catch {} //Added for popup windows.
	}
}
else {
	document.documentElement.setAttribute('data-theme', 'light');
}*/
document.documentElement.setAttribute('data-theme', 'light');

function switchTheme() {
	if (toggleSwitch) {
		if (toggleSwitch.checked) {
			document.documentElement.setAttribute('data-theme', 'dark');
			document.querySelectorAll("iframe").forEach((entry) => {
				try { entry.contentDocument.documentElement.setAttribute('data-theme', 'dark'); }
				catch {}
			});
			if (openwindows.length) {
				for (i=0; i < openwindows.length; i++) {
					if (!openwindows[i].closed) {
						openwindows[i].window.document.body.setAttribute('data-theme', 'dark');
					}
					else { openwindows.pop(i); i--; }
				}
			}
			// Condition not needed -- Acceptable consent through user action:
			/*if (localStorage.cookietypes) {*/ localStorage.setItem('theme', 'dark'); //}
		}
		else {
			document.documentElement.setAttribute('data-theme', 'light');
			document.querySelectorAll("iframe").forEach((entry) => {
				try { entry.contentDocument.documentElement.setAttribute('data-theme', 'light'); }
				catch {}
			});
			if (openwindows.length) {
				for (i=0; i < openwindows.length; i++) {
					if (!openwindows[i].closed) {
						openwindows[i].window.document.body.setAttribute('data-theme', 'light');
					}
					else { openwindows.pop(i); i--; }
				}
			}
			// Condition not needed -- Acceptable consent through user action:
			/*if (localStorage.cookietypes) {*/ localStorage.setItem('theme', 'light'); //}
		}
	}	
}

const custommarkup = Number(localStorage.getItem("overrideprice")) || 1;
const custommarkupD = Number(localStorage.getItem("overridepriceD")) || 1;

let headerpreview = document.getElementById("headerpreview");
let previewON = 1;

if (headerpreview) {
	const mobilequery1 = window.matchMedia("(max-width: 700px)");
	mobilequery1.addEventListener("change", function() { compareheaderwidth(); });
	const mobilequery2 = window.matchMedia("(max-width: 975px)");
	mobilequery2.addEventListener("change", function() { compareheaderwidth2(); });
}

function compareheaderwidth() {
	let topnav = document.querySelector("#topnav");
	let topcart = document.getElementById("topcart");
	let tim2 = document.getElementById("tabindexme2");
	
	//Swaps element properties to fit mobile view:
	if (window.innerWidth <= 700) {
		topnav.insertBefore(document.querySelector("#topsearchform"), topnav.children[0]);
		document.getElementById("homebtn").setAttribute("tabindex", 1);
		topcart.href = "/account/cart";
		topcart.removeAttribute("onclick");
		document.querySelector("#cartiframe").classList.add("hidden");
		document.querySelector("#cartamount").classList.remove("hidden");
		document.querySelector("#cartx").classList.add("hidden");
		document.getElementById("tabindexme").setAttribute("tabindex", 1);
		tim2.setAttribute("tabindex", 1);
		tim2.setAttribute("onfocus", "setnavcontent(6); document.getElementById('themecheckbox').focus()");
		document.getElementById("mobilenavBG").setAttribute("tabindex", 0);
		document.querySelector("#nme6 > .nmetables").innerHTML = "<div style='width: unset'>" + document.querySelector("#nme6 > .nmetables").innerHTML + "</div>";
	}
	//Swaps element properties to fit desktop view:
	else {
		topnav.insertBefore(document.querySelector("#topsearchform"), topnav.children[2]);
		document.getElementById("homebtn").removeAttribute("tabindex");
		topcart.href = "javascript:;";
		topcart.setAttribute("onclick", "cartpreview()");
		document.getElementById("tabindexme").removeAttribute("tabindex");
		tim2.removeAttribute("tabindex");
		tim2.setAttribute("onfocus", "setnavcontent(6)");
		document.getElementById("mobilenavBG").removeAttribute("tabindex");
		if (document.querySelector("#nme6 > .nmetables > div")) { //This only applies if the width was <= 700 at some point:
			document.querySelector("#nme6 > .nmetables > div").outerHTML = document.querySelector("#nme6 > .nmetables > div").innerHTML;
		}
	}
}
function compareheaderwidth2() { if (window.innerWidth < 975) { previewON = 0; } else { previewON = 1; } }

function addpreviewfuncs() {
	let previewlinks = navmainexpanded.querySelectorAll("[data-preview]");
	for (i=0; i < previewlinks.length; i++) {
		//console.log(currentvalue);
		previewlinks[i].setAttribute("onmouseenter", "swappreview(this)");
		previewlinks[i].setAttribute("onfocus", "swappreview(this)");
	}
	addsublinks();
}

function swappreview(caller) {
	if (previewON) {
		//First, set the background image to the image that's already there:
		headerpreview.parentElement.style.backgroundImage = "url(" + headerpreview.src + ")";
		//Fade the image out:
		headerpreview.style.opacity = "0%";
		//If the preview image is purposefully blank...
		if (caller.getAttribute("data-preview") === "blank") {
			//Hide the background:
			headerpreview.parentElement.style.backgroundImage = "unset";
			//Clear the image after fading (this makes it fade from emptiness when the function is called again):
			setTimeout(function() { headerpreview.src = ""; }, 200);
		}
		else {
			//Set the image as specified in the HTML data value (The image auto-sets its opacity on each load):
			setTimeout(function() {
				headerpreview.src = "/static/img/" + caller.getAttribute("data-preview") + ".jpg";
			}, 200);
		}
	}
}

function addsublinks() {
	let sublinks = navmainexpanded.querySelectorAll(".sublinks");
	let link;
	let btnlink;
	for (i=0; i < sublinks.length; i++) {
		link = sublinks[i].getAttribute("href");
		sublinks[i].setAttribute("onmouseenter", "this.href='" + link + "'; swappreview(this)");
		sublinks[i].setAttribute("onfocus", "this.href='" + link + "'; swappreview(this)");
		
		let btns = sublinks[i].querySelectorAll("button");
		for (y=0; y < btns.length; y++) {
			btnlink = btns[y].getAttribute("onclick").split("=")[1];
			btns[y].setAttribute("onmouseenter", "this.href=" + btnlink + "; this.parentElement.parentElement.href=" + btnlink);
			btns[y].setAttribute("onfocus", "this.href=" + btnlink + "; this.parentElement.parentElement.href=" + btnlink);
		}
	}
}

let wholeheader = document.querySelector("#topall");
function checktabbing(e) {
	console.log(e.buttons, e.target.className.includes('noCT'), e.target.getBoundingClientRect().top < 95, wholeheader.contains(e.target));
	console.log(e);
	//If no mouse buttons are down, AND target lacks the 'noCT' class, AND target is up and out of view, AND target is not in the header:
	if (!e.buttons && !e.target.className.includes('noCT') && e.target.getBoundingClientRect().top < 95 && !wholeheader.contains(e.target)) {
		console.log('Debugging: checktabbing triggered. \nTarget:', e.target, '\nActive element:', document.activeElement);
		window.scrollBy(0, -115 + e.target.getBoundingClientRect().top);
	}
}

function cartpreview() {
	document.querySelector("#cartamount").classList.toggle("hidden");
	document.querySelector("#cartx").classList.toggle("hidden");
	document.querySelector("#cartiframe").classList.toggle("hidden");
	//Prevents hover from triggering after close:
	document.querySelector("#topcart").setAttribute("onmouseenter", "");
}

function hovercart(el) {
	el.removeAttribute("onmouseenter");
	setTimeout(() => {
		if (window.innerWidth > 700 && document.querySelector("#topcart:not([onmouseenter]):hover:has(#cartx.hidden)")) {
			cartpreview();
		}
	}, 750);
}
function setCartCountDisplay(count) {
    const cartCountDisplay = document.querySelectorAll(".cart-count-display");
    let countParsed = 0;
    try {
        countParsed = typeof count === "string" ? parseInt(count) : count;
    } catch {
        countParsed = 0;
    }
    cartCountDisplay.forEach((entry) => {
        if (countParsed > 0) {
            entry.textContent = countParsed;
        } else {
            entry.textContent = '';
        }
    });
}
function refreshcartcount(glow) {
	fetch('/api/cart/', {
		method: "GET"
	}).then((response) => {
		if (response.ok) {
			response.json().then((json) => {
				if (typeof cartarray !== "undefined") { refreshcartarray(json.cart); }
				
				if (document.querySelector("#cartamount")) {
					let updatedcartcount = json.count;
					if (updatedcartcount > 999) {
						let humanappend = "K";
						
						//if (updatedcartcount > 999999) { humanappend = "M"; } else
						if (updatedcartcount > 99999) { updatedcartcount = "?"; humanappend = ""; }
						else if (updatedcartcount > 9999) { humanappend = updatedcartcount.toString()[1] + "K"; }
						
						//Get first digit and append the letter:
						updatedcartcount = updatedcartcount.toString()[0] + humanappend;
					}
					document.querySelector("#cartamount").textContent = updatedcartcount;

					if (glow) { document.querySelector("#topcart").classList.add("adjusted"); }
				}
				
				try { document.querySelector("#cartnum").textContent = json.count; 
					

				} catch {}
				try { document.querySelector("#cartnumv2").textContent = json.count||""; } catch {}
				try { setCartCountDisplay(json.count); } catch {}
				try{
					// list of cart count display
					const cartCountDisplay = document.querySelectorAll(".cart-count-display");
					cartCountDisplay.forEach((entry) => {
						entry.innerHTML = json.count;
					});
				} catch {}
				//Refresh the iframe, but dont force it if it's not open:
				document.querySelector("#cartiframe").src += "";
			});
		}
	});
}

/*let spanimation;
function updatemetalmarket() {
	fetch('/api/kitco-metal-market/', {
		method: "GET"
	}).then((response) => {
		if (response.ok) {
			response.json().then((json) => {
				let spanner = document.querySelector("#metalspanner");
				let mm = 0;
				let fillmm = "";
				for (quicki = 0; quicki < 4; quicki++) {
					fillmm += "<h5>" + Object.keys(json.market)[quicki] + ": " + (Object.values(json.market)[quicki].price).toLocaleString("en-US", {style:"currency", currency:"USD"});
					if (Object.values(json.market)[quicki].movement == "Up") {
						fillmm += " <i class='fa fa-solid fa-caret-up' style='color: #0bb335'></i>";
					}
					else if (Object.values(json.market)[quicki].movement == "down") {
						fillmm += " <i class='fa fa-solid fa-caret-down' style='color: #ec3c3c'></i>";
					}
					else {
						fillmm += " <i class='fa fa-solid fa-minus' style='color: var(--colorlink); transform: scale(0.8);'></i>";
					}
					fillmm += "</h5>";
					
					//First loop only: Add the gold value to the version seen when printing the page:
					if (!quicki) {
						spanner.previousElementSibling.innerHTML = fillmm;
					}
				}
				spanner.nextElementSibling.innerHTML = fillmm;
				
				function updatespanner() {
					spanner.innerHTML = spanner.nextElementSibling.children[mm].innerHTML;
				}
				
				spanner.style.animationPlayState = "running";
				setTimeout(() => {
					updatespanner();
					spanimation = setInterval(() => {
						mm++;
						if (mm >= 4) { mm = 0; }
						updatespanner();
					}, 5000);
				}, 1000);
			});
		}
	});
}*/

/* Return proper capitalization with a new .toProperCase() function: */
String.prototype.toProperCase = function () {
    return this.replace(/\w\S*/g, function(txt){return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();});
};

let collectionslist;
//Give the user some time to type before processing their search:
let cachedsearch = "";
function checksearch(val) {
	cachedsearch = val;
	
	//Only search if inputs stopped within the last half-second:
	setTimeout(() => {
		if (val == cachedsearch && val.trim().length) { topsearch(val); }
	}, 500);
	
	if (typeof collectionslist == 'undefined') {
		collectionslist = 'placeholderstring';
		fetch('/static/collectionlist.json', {
			method: "GET"
		}).then((response) => {
			if (response.ok) {
				response.json().then((json) => { collectionslist = json; });
			}
		});
	}
}

//Go through with the search:
function topsearch(val) {
	val = val.trim().replace("#", "").replace("&", "and").replaceAll("'", "").toProperCase();
	
	let tsprod = document.querySelector("#tsprod");
	tsprod.innerHTML = '<a id="emptysearchresults">Searching...<img src="/static/img/icons/loading.svg"></a>';
	tsprod.nextElementSibling.innerHTML = "";
	
	let searchdiamonds = 0;
	
	fetch('/api/search_suggestions/?q=' + val, {
		method: "GET"
	}).then((response) => {
		if (response.ok) {
			response.json().then((json) => {
				//Add each result to one variable:
				let allresults = "";
				
				//If the search is not a syntax that would match a diamond lot number (Letter, Letter/Number, Number),
				//search known collections:
				if (!val.toUpperCase().match(/^[BN][A-Z0-9]\d/)) {
					Object.keys(collectionslist).forEach((key) => {
						if (key.includes(val)) {
							allresults += "<a href='/" + collectionslist[key]['url'] + "'>"
										+ "<img src='" + collectionslist[key]['images'] + "' class='collimg' role='decoration'>"
										+ "<img src='" + collectionslist[key]['images'] + "' class='collimg' role='decoration'>"
										+ "<span class='outlineonly' aria-hidden='true'>" + key.split("||")[0] + "</span>"
										+ "<span>" + key.split("||")[0] + "</span>"
										+ "</a>"
							;
						}
					});
					if (allresults) {
						allresults = "<h4 tabindex='-1'>Collections / Services</h4>" + allresults;
					}
				}
				//If it does match diamond syntax:
				else {
					searchdiamonds = 1;
					allresults = "<h4 tabindex='-1'>Diamonds (Searching...)</h4>";
				}
				
				//Set the collections or diamonds display to the results:
				tsprod.nextElementSibling.innerHTML = allresults;
				
				if (json.products.length) {
					allresults = "<h4 tabindex='-1'>Products</h4>";
					for (i=0; i < json.products.length; i++) {
						const imglink = json.products[i].images || "/static/img/nostone.jpg";
						
						allresults += "<a href='/product/" + json.products[i].url + "'>"
									+ "<img src='" + imglink + "' role='decoration'>"
									+ "<img src='" + imglink + "' role='decoration'>"
									+ "<span class='outlineonly' aria-hidden='true'>" + json.products[i].style_number + "</span>"
									+ "<span>" + json.products[i].style_number + "</span>"
									+ "</a>"
						;
					}
				}
				else if (!allresults) { //If the collections/diamonds section was also empty:
					allresults = "<a id='emptysearchresults'>No results found.</a>";
				} //If the collections section was not empty:
				else { allresults = ""; }
				
				//Set the collections display to the results:
				tsprod.innerHTML = allresults;
				
				//Search the diamonds after all that:
				if (searchdiamonds) {
					finddiamonds();
				}
			});
		}
	});
	
	function finddiamonds() {
		let which = "lab";
		if (val.startsWith("N")) {
			which = "natural";
		}
		
		tsprod.nextElementSibling.innerHTML = '<a id="emptysearchresults">Searching Diamonds...<img src="/static/img/icons/loading.svg"></a>';
		
		fetch('/api/diamonds/' + which + '/?lot_number=' + val, {
			method: "GET"
		}).then((response) => {
			if (response.ok) {
				response.json().then((json) => {
					//Add each result to one variable:
					let allresults = "<h4 tabindex='-1'>Diamonds</h4>";
					
					for (i=0; i < json.diamonds.length; i++) {
						const imglink = json.diamonds[i].image_url || "/static/img/nostone.jpg";
						
						allresults += "<a href='/diamonds/" + which + "/?lot_number=" + json.diamonds[i].lot_number + "'>"
									+ "<img src='" + imglink + "' role='decoration'>"
									+ "<img src='" + imglink + "' role='decoration'>"
									+ "<span class='outlineonly' aria-hidden='true'>" + json.diamonds[i].lot_number + "</span>"
									+ "<span>" + json.diamonds[i].lot_number + "</span>"
									+ "</a>"
						;
					}
					
					if (!json.diamonds.length) { //If the diamonds section was empty:
						allresults = "<a id='emptysearchresults'>No diamonds found.</a>";
					}
					else {
						document.querySelector("#vas2").href = '/diamonds/' + which + '/?lot_number=' + val;
					}
					//Set the diamonds display to the results:
					tsprod.nextElementSibling.innerHTML = allresults;
				});
			}
		});
	}
}

function searchsubmit() {
	//If there's only one result, just go to that product's url. Otherwise, go to the search page:
	/*if (document.querySelector("#topsearchresults > #tsprod > a[href]:only-of-type")) {
		document.querySelector("#topsearchresults > #tsprod > a[href]").click()
	}*/
	if (document.querySelector("#search-show > a[href]:only-of-type")) {
		document.querySelector("#search-show > a[href]").click()
	}
	else {
		searchfull();
	}
}

function searchfull() {
	//Go to the standalone search page:
	//location.href = "/search?q=" + document.querySelector("#topsearch").value.replace("#", "");
	location.href = "/search?q=" + document.querySelector("#search-content").value.replace("#", "");
}

function catnavigate(e, url, jumper) {
	//Mouse clicked on the category:
	if (e.detail) {
		//Go to specified location:
		location.href = url;
	}
	//Enter was pressed on the category:
	else {
		//Jump to specified element:
		refocus(jumper);
	}
}

function confirmlogout() {
	const logform = document.querySelector("#logoutform");
	if (window.confirm("Are you sure you want to log out?")) {
		//Use the header form to sign out:
		if (logform) {
			document.querySelector("#logoutform").submit();
		}
		//Fallback -- Make a post request and refresh:
		else if (document.querySelector("input[name='csrfmiddlewaretoken']")) {
			fetch('/account/logout/', {
				method: "POST",
				headers: {
					"X-CSRFToken": document.querySelector("[name='csrfmiddlewaretoken']").value
				}
			}).then((response) => {
				if (response.ok) {
						window.location.reload();
				}
			});
		}
		//Logout failed -- Let the user know:
		else {
			sysalert('Error logging out! Please try again on a different page.', '');
		}
	}
}

function closesitealert(warning) {
	// Condition not needed -- Acceptable consent through user action:
	//if (localStorage.cookietypes) {
		localStorage.closedalert += warning.id + ","; //Change this value when a new alert is pushed.
	//}
	
	warning.remove();
}

function opensitealerts() {
	let closedalerts = "";
	if (localStorage.closedalert) {
		closedalerts = localStorage.closedalert.split(",");
	}
	//Cycle through the sitewide alerts and display ones that haven't been closed yet:
	document.querySelectorAll(".warning.hidden").forEach((entry) => {
		if (!closedalerts.includes(entry.id)) {
			entry.classList.remove("hidden");
		}
	});
}
opensitealerts();

let fadeblock = false;
function fadeelements(sooner) {
	//If any fade-enabled elements exist, find them:
	if (!fadeblock && document.querySelector("[data-fadein]:not([data-fadein='fade'], [data-fading])")) {
		let faders = document.querySelectorAll("[data-fadein]:not([data-fadein='fade'], [data-fading])");
		//Set the amount of pixels from the bottom for the elements to animate, capped at 200 pixels:
		let threshold;
		if (!sooner) { threshold = Math.min((window.innerHeight / 5), 200); }
		else if (sooner == "soonest") { threshold = Math.min((window.innerHeight / 20), 50); }
		else { threshold = Math.min((window.innerHeight / 10), 100); }
		
		let timeoffset = 100;
		let translateoffset = 50;
		
		for (i=0; i < faders.length; i++) {
			let action = faders[i].getAttribute("data-fadein");
			if (action.startsWith("up")) { translateoffset = 50; }
			else if (action.startsWith("down")) { translateoffset = -50; }
			else { translateoffset = 0; }
			
			//If the top of an element is within the view, offset by 1/5th of the screen height (or 200 pixels):
			if (faders[i].getBoundingClientRect().top < window.innerHeight + translateoffset - threshold) {
				
				faders[i].setAttribute("data-fading", "1");
				
				function fadeout(x) {
					//Carry out the fade:
					faders[x].setAttribute("data-fadein", "fade");
					faders[x].removeAttribute("data-fading");
				}
				
				//If this element is next to the previous element, wait a tiny moment before fading in:
				if (i && !action.endsWith("synced") && Math.abs(faders[i].getBoundingClientRect().top - faders[i-1].getBoundingClientRect().top) <= 50) {
					//Uses the value of i in its current state:
					let x = i;
					//Queues the fade-in for 100ms after the last:
					setTimeout(() => { fadeout(x); }, timeoffset);
					//Increase the time for the next one if it will exist:
					timeoffset = timeoffset + 100;
				}
				else {
					fadeout(i);
					timeoffset = 100;
				}
			}
		}
	}
}
window.onscroll = function () { fadeelements(); }