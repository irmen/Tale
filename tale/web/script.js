"use strict";

function setup()
{
    var but=document.getElementById("button-autocomplete");
    if(but.accessKeyLabel) { but.value += ' ('+but.accessKeyLabel+')'; }

    document.text_refresher = setInterval(poll_text, 450);
    window.onbeforeunload = function(e) { return "Are you sure you want to abort the session and close the window?"; }
}

function poll_text() {
    var txtdiv = document.getElementById("textframe");
    var ajax = new XMLHttpRequest();
    ajax.onreadystatechange = function() {
        var DONE = this.DONE || 4;
        if (this.readyState === DONE) {
            if(this.status>=300) {
                txtdiv.innerHTML += "<p><em>Server error: "+this.responseText+"</em><br><em>Perhaps refreshing the page might help.</em></p>"
                txtdiv.scrollTop = txtdiv.scrollHeight;
                clearInterval(document.text_refresher);
                return;
            }
            var json = JSON.parse(this.responseText);
            if(json["text"]) {
                document.getElementById("player-location").innerHTML = json["location"];
                document.getElementById("player-turns").innerHTML = json["turns"];
                txtdiv.innerHTML += json["text"];
                txtdiv.scrollTop = txtdiv.scrollHeight;
            }
            var special = json["special"];
            if(special) {
                if(special.indexOf("clear")>=0) {
                    txtdiv.innerHTML = "";
                    txtdiv.scrollTop = 0;
                }
            }
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
    if(cmd_input.value) {
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
    }
    cmd_input.focus();
    return false;
}

function quit_clicked() {
    if(confirm("Quitting like this will abort your game.\nYou will lose your progress. Are you sure?")) {
        window.onbeforeunload = null;
        document.location="quit";
        return true;
    }
    return false;
}
