// Objects for storing ball heat, for CSS functionality
const balls = {
	cold: [],
	hot: []
}
const pBalls = {
	cold: [],
	hot: []
}

const previousBalls = {
	cold: [],
	hot: []
}

const previousPBalls = {
	cold: [],
	hot: []
}


// Function to catagorize ball heat from html output from backend
const returnNumbers = function(element) {

	// Access the child elements - in this case the ball numbers
	const elements = element.getElementsByTagName('span');

	// Process number sequences based on HTML id
	switch (element.id) {
		case 'cold':
			for (let i = 0; i < elements.length; i++) {
				balls.cold.push(parseInt(elements[i].innerHTML, 10));
			}
			break;
		case 'hot':
			for (let i = 0; i < elements.length; i++) {
				balls.hot.push(parseInt(elements[i].innerHTML, 10));
			}
			break;
		case 'coldP':
			for (let i = 0; i < elements.length; i++) {
				pBalls.cold.push(parseInt(elements[i].innerHTML, 10));
			}
			break;
		case 'hotP':
			for (let i = 0; i < elements.length; i++) {
				pBalls.hot.push(parseInt(elements[i].innerHTML, 10));
			}
			break;
		case 'previousCold':
			for (let i = 0; i < elements.length; i++) {
				previousBalls.cold.push(parseInt(elements[i].innerHTML, 10));
			}
			break;
		case 'previousHot':
			for (let i = 0; i < elements.length; i++) {
				previousBalls.hot.push(parseInt(elements[i].innerHTML, 10));
			}
			break;
		case 'previousColdP':
			for (let i = 0; i < elements.length; i++) {
				previousPBalls.cold.push(parseInt(elements[i].innerHTML, 10));
			}
			break;
		case 'previousHotP':
			for (let i = 0; i < elements.length; i++) {
				previousPBalls.hot.push(parseInt(elements[i].innerHTML, 10));
			}
		break;
		default:
			console.log('Error detirmining which balls are hot and cold.');
	}
}


// Function to set session storage for access to ball heat across pages
const populateStorage = function() {
	// https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API/Using_the_Web_Storage_API
	sessionStorage.setItem('coldBalls', JSON.stringify(balls.cold));
	sessionStorage.setItem('hotBalls', JSON.stringify(balls.hot));
	sessionStorage.setItem('coldPBalls', JSON.stringify(pBalls.cold));
	sessionStorage.setItem('hotPBalls', JSON.stringify(pBalls.hot));
}


// Check if number in array & return boolean
const color = function(num, catagory) {
	if (catagory === 'ball') {
		// Return true if num matches a cold ball else false
		for (let x = 0; x < balls.cold.length; x++) {
			if (num === balls.cold[x]) {
				return true;
			}
		}
		return false;
	}

	if (catagory === 'pBall') {
		// Return true if num matches a cold ball else false
		for (let x = 0; x < pBalls.cold.length; x++) {
			if (num === pBalls.cold[x]) {
				return true;
			}
		}
		return false;
	}

	if (catagory === 'previousBall') {
		// Return true if num matches a cold ball else false
		for (let x = 0; x < previousBalls.cold.length; x++) {
			if (num === previousBalls.cold[x]) {
				return true;
			}
		}
		return false;
	}

	if (catagory === 'previousPBall') {
		// Return true if num matches a cold ball else false
		for (let x = 0; x < previousPBalls.cold.length; x++) {
			if (num === previousPBalls.cold[x]) {
				return true;
			}
		}
		return false;
	}
}


// Add rows to form table
let rowCount = 2;

const addRow = function() {
	// Get table body to append to
	let tbody = document.querySelector('tbody');

	/* 	Clone the last row in the table - the first clonable row of the table is the 3rd tr which allows us to use rowCount
		which is doubling as the concatenated integer counter for the name attribute for each row */
	const row = document.querySelectorAll('tr')[rowCount];

	// Clone node and update name attributes - essential for back end parsing 
	const newRow = row.cloneNode(true);
	const cells = newRow.querySelectorAll('td');
	cells[0].querySelector('select').setAttribute('name', 'hot' + rowCount);
	cells[1].querySelector('select').setAttribute('name', 'power' + rowCount);
	cells[2].querySelector('select').setAttribute('name', 'count' + rowCount);

	// Disable the button on the row that has been cloned
	row.getElementsByTagName('td')[3].style.display = "none";

	// Increase row counter
	rowCount++;

	// Append new row to table
	tbody.appendChild(newRow);
}


// Copy script to clipboard
const copyScript = function () {
	// I got help with this from https://www.30secondsofcode.org/articles/s/copy-text-to-clipboard-with-javascript
	const el = document.createElement('textarea');
	el.value = fill;
	el.setAttribute('readonly', '');
	el.style.position = 'absolute';
	el.style.left = '-9999px';
	document.body.appendChild(el);
	el.select();
	document.execCommand('copy');
	document.body.removeChild(el);
	alert('Script has been copied to clipboard');
}

