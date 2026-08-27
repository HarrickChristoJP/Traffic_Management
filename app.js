import { createClient } from "https://esm.sh/@supabase/supabase-js";

// Paste your team's values here later.
const SUPABASE_URL = "https://fpiwqwxbsttmlektirgg.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZwaXdxd3hic3R0bWxla3RpcmdnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODYxNDk2NDcsImV4cCI6MjEwMTcyNTY0N30.U0ubME9xN4SPi1NMeZ_vODbpeYNCrS4_4VT2FWaUlzE";

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const loginBtn = document.getElementById("loginBtn");
const message = document.getElementById("message");

loginBtn.addEventListener("click", async () => {

    const signalID = document.getElementById("signalID").value.trim();
    const officerID = document.getElementById("officerID").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!signalID || !officerID || !password) {
        message.style.color = "red";
        message.textContent = "Please fill all fields.";
        return;
    }

    message.style.color = "#0F4C81";
    message.textContent = "Connecting to database...";
    const { data, error } = await supabase
    .from("signals")
    .select("*")
    .limit(1);

if (error) {
    message.style.color = "red";
    message.textContent = "Database connection failed!";
    console.error(error);
} else {
    message.style.color = "green";
    message.textContent = "Connected to Supabase successfully!";
    console.log(data);
}

});