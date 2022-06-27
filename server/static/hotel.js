



function ajax() {
var item = document.querySelector('#recommendations').value
var req = new XMLHttpRequest();
req.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var data = this.response
            layout(data)
        }
    };

    req.open("GET", "/recommendation_query?item="+item, true);
    req.responseType = 'json'
    req.send();
}