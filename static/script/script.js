const sleep = ms => new Promise(res => setTimeout(res, ms))

const resize = () => {
    const body = document.querySelector("body")
    const sidebar = document.querySelector("#sidebar");

    body.style.height = window.innerHeight + 'px';
    sidebar.style.width = window.innerWidth / 6 + 'px';
    if (window.innerWidth < 500) {
        body.classList.add("sp");
        sidebar.classList.add("close");
    } else {
        body.classList.remove("sp")
        sidebar.classList.remove("close");
    }
}
const send_file = (base64) => {
    let body = { "note_id": note_id }
    let data = base64.split(/(:|,|;)/)
    if ("application/pdf" == data[2]) {
        body["pdf"] = data[6]
    } else if (data[2].match(/^image\/\w{2,5}$/g)) {
        body["image"] = data[6]
    } else {
        body["docs"] = data[6]
    }
    fetch("/add", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(res => res.json()).then(data => {
        if (data["status"]) {
            location.reload()
        } else {
            alert("送信失敗")
        }
    })
}
const upload_file = () => {
    const dummy_button = document.createElement("input");
    dummy_button.type = "file";
    dummy_button.addEventListener("change", () => {
        const reader = new FileReader();
        const image = new Image();
        reader.onload = () => {
            send_file(reader.result);
        };
        reader.readAsDataURL(dummy_button.files[0]);
    });
    dummy_button.click();
};

const export_file = () => {
    page_num = prompt("出力するページ", "0-3,5 or all");
    if (page_num === null) {

    } else if (page_num == "all" || page_num === "") {
        open("/data/" + note_id)
    } else if (page_num.length > 0) {
        open(`/export/${note_id}?page_num=${page_num}`)
    }
}

window.onload = () => {
    resize()
    window.onresize = resize

    document.querySelector("img#menu").addEventListener("click", () => {
        const sidebar = document.querySelector("#sidebar");
        if (sidebar.classList.contains("close")) {
            sidebar.style.width = window.innerWidth / 6 + 'px';
            (async () => {
                await sleep(500);
                sidebar.classList.remove("close")
            })();
        } else {
            sidebar.classList.add("close")
            sidebar.style.width = '0px';
        }
    })

    document.querySelector("img#upload").addEventListener("click", upload_file)
    document.querySelector("img#export").addEventListener("click", export_file)


    const title = document.querySelector("#toolbar h1").textContent
    document.querySelectorAll("#sidebar a").forEach((elm) => {
        if (elm.id == note_id) {
            elm.children[0].classList.add("select")
        }
    })

    document.querySelector("#sidebar input#create").addEventListener("click", () => {
        const notename = prompt("新しいノートの名前を入れてください", "New Notebook")
        if (notename) {
            let body = { "title": notename }
            fetch("/create", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(res => res.json()).then(data => {
                if (data["status"]) {
                    location.reload()
                } else {
                    alert("送信失敗")
                }
            })
        }
    })


    let select_note = "";
    document.querySelectorAll("#sidebar ul a").forEach((elm) => {
        const menu = document.querySelector("div#contextmenu")
        elm.addEventListener('contextmenu', function (event) {
            select_note = elm.id;
            event.preventDefault()
            menu.classList.remove("d-none")
            menu.style.top = event.clientY + 'px'
            menu.style.left = event.clientX + 'px'
        })
    })
    document.querySelector("#toolbar h1").addEventListener("click", () => {
        const menu = document.querySelector("div#contextmenu")
        menu.classList.add("d-none")
    })
    document.querySelector("#contextmenu input#remove").addEventListener("click", (event) => {
        let body = { "note_id": select_note }
        fetch("/remove", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }).then(res => res.json()).then(data => {
            if (data["status"]) {
                location.reload()
            } else {
                alert("送信失敗")
            }
        })

    })


    let context = '<iframe class="preview" src="/static/web/viewer.html?file=/data/' + note_id + '" frameborder="0" loading="lazy"></iframe>';
    (async () => {
        await sleep(50);
        document.querySelector("#document").insertAdjacentHTML("afterbegin", context);
    })();
}