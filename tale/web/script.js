"use strict";

function setup()
{
    var but=document.getElementById("button-autocomplete");
    if(but.accessKeyLabel) { but.value += ' ('+but.accessKeyLabel+')'; }

    document.text_refresher = setInterval(poll_text, 500);
}

function poll_text() {
    var txtdiv = document.getElementById("textframe");
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        var DONE = this.DONE || 4;
        if (this.readyState === DONE) {
            var match = this.responseText.match(/@tale-location:@ {{(.+?)}}/);
            if(match) {
                var location = match[1];
                document.getElementById("player-location").innerHTML = location;
            }
            var match = this.responseText.match(/@tale-turns:@ {{(.+?)}}/);
            if(match) {
                var turns = match[1];
                document.getElementById("player-turns").innerHTML = turns;
            }
            txtdiv.innerHTML += this.responseText;
            txtdiv.scrollTop = txtdiv.scrollHeight;
        }
    }
    ajax.onerror = function(error) {
        txtdiv.innerHTML="<strong>Connection error.</strong><br><br><p>Close the browser or refresh the page.</p>";
        clearInterval(document.text_refresher);
        var cmd_input = document.getElementById("input-cmd");
        cmd_input.disabled=true;
    }
    ajax.open("GET", "text", true);
    ajax.send(null);
}

function submit_cmd() {
    var cmd_input = document.getElementById("input-cmd");
    if(!cmd_input.value)
        return false;
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        var DONE = this.DONE || 4;
        if(this.readyState==DONE) {
            setTimeout(poll_text, 100);
        }
    }
    ajax.open("POST", "input", true);
    ajax.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    ajax.send("cmd=" + encodeURIComponent(cmd_input.value));
    cmd_input.value="";
    cmd_input.focus();
    return false;
}

function autocomplete_cmd() {
    var cmd_input = document.getElementById("input-cmd");
    if(!cmd_input.value)
        return false;
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        var DONE = this.DONE || 4;
        if(this.readyState==DONE) {
            setTimeout(poll_text, 100);
        }
    }
    ajax.open("POST", "input", true);
    ajax.setRequestHeader("Content-type","application/x-www-form-urlencoded");
    ajax.send("cmd=" + encodeURIComponent(cmd_input.value)+"&autocomplete=1");
    cmd_input.focus();
    return false;
}
