const usp = new URLSearchParams(new URL(window.location).search);

let cats = new Array();

for (const [key, val] of usp) {
    if (key === "categories") {
        cats.push(val);
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function get(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(error.message);
    }
}

function compare(a, b) {
    if (a.place !== 0 && b.place !== 0) {
        return a.place - b.place;
    }
    if (a.status === "?" && b.status === "?") {
        return a.name > b.name;
    }
    if (a.status === "?" && b.status !== "OK") {
        return -1;
    }
    if (a.status !== "OK" && b.status === "?") {
        return 1;
    }
}

function animateProgress($progressBar, val, currentVal) {
    currentVal = currentVal || 0;

    var step = val * 16 / 500;

    function animate(currentVal) {
        currentVal += step;

        $progressBar.val(currentVal);

        currentVal < val && requestAnimationFrame(function () {
            animate(currentVal);
        });
    }

    animate(currentVal);
}

async function mainProc() {
    document.body.requestFullscreen();
    document.querySelector("#categories").innerHTML = cats.join(", ");
    const results_elem = document.querySelector("#results-table");
    const ann_elem = document.querySelector("#ann");
    while (true) {
        online_cats = await get("/api/categories")
        for (const cat of cats) {
            ann_elem.style.display = "none";
            document.querySelector("#progress-bar").style = "transition: width .2ss; width: 0%;"
            document.querySelector("#cat-name").textContent = cat;
            document.querySelector("#cat-controls").textContent = online_cats[cat];
            let results = await get(`/api/results?category=${cat}`);
            results_elem.innerHTML = "";

            // results.sort(compare);

            if (results.length === 0) {
                ann_elem.style.display = "flex";
                ann_elem.children[0].textContent = "NIKDO 🙈";
            } else {
                for (const result of results) {
                    let place = result.place > 0 ? result.place > 4 ? `${result.place}.` : ["🥇", "🥈", "🥉", "🥔"][result.place - 1] : result.time === "UNS" ? "🛌🏿" : result.status === "?" ? "🏃🏾‍➡️" : result.status;
                    const in_forest = result.status === "?";
                    const show_info = ["OK", "OVT", "MP"].includes(result.status);
                    const ok = result.status === "OK";
                    const order = result.order.map((x) => `<b>${x[0]}</b> - ${x[1]}`).join(", ");
                    results_elem.innerHTML += `<tr><td class="place"><b>${place}</b></td><td><b>${result.name}${result.index === "ELB0904" ? " 👨🏿‍💻" : result.index === "AFK1003" ? " 🎨" : ""}</b></td><td>${result.index}</td><td class="time"><b>${!ok && show_info ? `<span class="invalid">` : ""}${in_forest ? `<span class="temp_res">` : ""}${!(show_info || in_forest) ? "" : result.time === "UNS" ? `S: ${result.start}` : result.time}${in_forest ? "</span>" : ""}${!ok && show_info ? `</span>` : ""}</b></td><td class="tx"><b>${!ok && show_info ? `<span class="invalid">` : ""}${show_info ? `${result.tx} TX` : "-"}${!ok && show_info ? `</span>` : ""}</b></td><td>${!ok && show_info ? `<span class="invalid">` : ""}${show_info ? order : ""}${!ok && show_info ? `</span>` : ""}</td></tr>`
                }
            }
            await sleep(200);
            let time = results.length === 0 ? 1500 : Math.max(5000, results.length * 750);
            document.querySelector("#progress-bar").style = `transition: width ${time / 1000}s linear; width: 100%;`;
            await sleep(time);
        }
        let announcement = await get(`/api/announcement`);
        if (announcement !== "") {
            results_elem.innerHTML = "";
            ann_elem.children[0].innerHTML = announcement;
            document.querySelector("#cat-name").textContent = "HLÁŠENÍ";
            document.querySelector("#cat-controls").textContent = "";
            ann_elem.style.display = "flex";
            document.querySelector("#progress-bar").style = "transition: width .2ss; width: 0%;"
            await sleep(200);
            document.querySelector("#progress-bar").style = `transition: width ${10}s linear; width: 100%;`;
            await sleep(10000);
            ann_elem.style.display = "none";
        }
    }
}

mainProc();





