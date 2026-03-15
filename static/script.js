async function doSearch(){

    const query = document.getElementById("query").value;

    if(!query) return;

    const response = await fetch("/search?q=" + encodeURIComponent(query));

    const data = await response.json();

    const resultsDiv = document.getElementById("results");

    resultsDiv.innerHTML = "";

    if(data.length === 0){
        resultsDiv.innerHTML = "<p>Ничего не найдено</p>";
        return;
    }

    data.forEach(r => {

        const div = document.createElement("div");

        div.className = "result";

        const title = highlight(r.doc, query);

        const snippet = highlight(r.snippet, query);

        div.innerHTML =
        `<div class="doc">
            <a href="${r.url}" target="_blank">${title}</a>
        </div>
        
        <div class="snippet">
            ${snippet}
        </div>
        
        <div class="score">
            релевантность: ${r.score.toFixed(5)}
        </div>`;

        resultsDiv.appendChild(div);

    });

}

function highlight(text, query){

    const words = query.split(" ");

    words.forEach(w=>{
        const regex = new RegExp(`(${w})`, "gi");
        text = text.replace(regex, "<mark>$1</mark>");
    });

    return text;
}