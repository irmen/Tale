"use strict";

function setup()
{
    var but=document.getElementById("button-autocomplete");
    if(but.accessKeyLabel) { but.value += ' ('+but.accessKeyLabel+')'; }

    document.smoothscrolling_busy = false;
    window.onbeforeunload = function(e) { return "Are you sure you want to abort the session and close the window?"; }

    // use eventsource (server-side events) to update the text, rather than manual ajax polling
    var esource = new EventSource("eventsource");
    esource.addEventListener("text", function(e) {
        process_text(JSON.parse(e.data));
    }, false);
    esource.addEventListener("message", function(e) {
        console.log("eventsource unclassified message", e.lastEventId, e.data);
    }, false);

    esource.addEventListener("error", function(e) {
        console.error("eventsource error:", e, e.target.readyState);
        var txtdiv = document.getElementById("textframe");
        if(e.target.readyState == EventSource.CLOSED) {
            txtdiv.innerHTML += "<p class='server-error'>Connection closed.<br><br>Refresh the page to restore it. If that doesn't work, quit or close your browser and try with a new window.</p>";
        } else {
            txtdiv.innerHTML += "<p class='server-error'>Connection error.<br><br>Perhaps refreshing the page fixes it. If it doesn't, quit or close your browser and try with a new window.</p>";
        }
        var cmd_input = document.getElementById("input-cmd");
        cmd_input.disabled=true;
        //   esource.close();       // close the eventsource, so that it won't reconnect
    }, false);
}

function process_text(json)
{
    var txtdiv = document.getElementById("textframe");
    if(json["error"]) {
        txtdiv.innerHTML += "<p class='server-error'>Server error: "+JSON.stringify(json)+"<br>Perhaps refreshing the page might help. If it doesn't, quit or close your browser and try with a new window.</p>";
        txtdiv.scrollTop = txtdiv.scrollHeight;
    }
    else
    {
        var special = json["special"];
        if(special) {
            if(special.indexOf("clear")>=0) {
                txtdiv.innerHTML = "";
                txtdiv.scrollTop = 0;
            }
        }
        if(json["text"]) {
            document.getElementById("player-location").innerHTML = json["location"];
            // document.getElementById("player-turns").innerHTML = json["turns"];
            txtdiv.innerHTML += json["text"];
            if(!document.smoothscrolling_busy) smoothscroll(txtdiv, 0);
        }
    }
}


function smoothscroll(div, previousTop)
{
    document.smoothscrolling_busy = true;
    if(div.scrollTop < div.scrollHeight) {
        div.scrollTop += 6;
        if(div.scrollTop > previousTop) {
            window.requestAnimationFrame(function(){smoothscroll(div, div.scrollTop);});
            // setTimeout(function(){smoothscroll(div, div.scrollTop);}, 10);
            return;
        }
    }
    document.smoothscrolling_busy = false;
}


function submit_cmd()
{
    var cmd_input = document.getElementById("input-cmd");
    var ajax = new XMLHttpRequest();
    ajax.open("POST", "input", true);
    ajax.setRequestHeader("Content-type","application/x-www-form-urlencoded; charset=UTF-8");
    var encoded_cmd = encodeURIComponent(cmd_input.value);
    ajax.send("cmd=" + encoded_cmd);
    cmd_input.value="";
    cmd_input.focus();
    return false;
}

function autocomplete_cmd()
{
    var cmd_input = document.getElementById("input-cmd");
    if(cmd_input.value) {
        var ajax = new XMLHttpRequest();
        ajax.open("POST", "input", true);
        ajax.setRequestHeader("Content-type","application/x-www-form-urlencoded");
        ajax.send("cmd=" + encodeURIComponent(cmd_input.value)+"&autocomplete=1");
    }
    cmd_input.focus();
    return false;
}

function quit_clicked()
{
    if(confirm("Quitting like this will abort your game.\nYou will lose your progress. Are you sure?")) {
        window.onbeforeunload = null;
        document.location="quit";
        return true;
    }
    return false;
}
