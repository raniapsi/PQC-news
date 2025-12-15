document.addEventListener("DOMContentLoaded", async () => {
    const newsList = document.getElementById("news-list");
    
    // Add loading message
    newsList.innerHTML = "<p>Chargement des actualités...</p>";

    try {
        const apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? "http://127.0.0.1:8000/news"
            : "/news";
        
        console.log("Fetching from:", apiUrl);
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const newsData = await response.json();
        console.log("Received data:", newsData);
        
        // Clear loading message
        newsList.innerHTML = "";

        const entries = Object.entries(newsData);
        if (entries.length === 0) {
            newsList.innerHTML = "<p>Aucune donnée d'actualités disponible.</p>";
            return;
        }

        entries.forEach(([category, articles]) => {
            const categoryTitle = document.createElement("h2");
            categoryTitle.textContent = category;
            categoryTitle.style.marginTop = "30px";
            categoryTitle.style.marginBottom = "15px";
            newsList.appendChild(categoryTitle);

            if (!articles || articles.length === 0) {
                const empty = document.createElement("p");
                empty.textContent = "Aucun article pour cette catégorie.";
                newsList.appendChild(empty);
                return;
            }

            const articleList = document.createElement("ul");
            articleList.style.listStyle = "none";
            articleList.style.padding = "0";

            articles.forEach(article => {
                const listItem = document.createElement("li");
                listItem.style.marginBottom = "15px";
                listItem.style.paddingBottom = "15px";
                listItem.style.borderBottom = "1px solid #eee";

                const link = document.createElement("a");
                link.href = article.url;
                link.textContent = article.title;
                link.target = "_blank";
                link.style.display = "block";
                link.style.marginBottom = "5px";
                link.style.color = "#0066cc";
                link.style.textDecoration = "none";

                listItem.appendChild(link);

                // Affiche le domaine source
                try {
                    const domain = new URL(article.url).hostname.replace(/^www\./, "");
                    const source = document.createElement("small");
                    source.textContent = `Source: ${domain}`;
                    source.style.color = "#666";
                    listItem.appendChild(source);
                } catch (e) {
                    console.warn("Invalid URL:", article.url);
                }

                articleList.appendChild(listItem);
            });

            newsList.appendChild(articleList);
        });
    } catch (error) {
        console.error("Erreur lors de la récupération des actualités :", error);
        newsList.innerHTML = `
            <p style="color: red;">Erreur lors du chargement des actualités.</p>
            <p style="color: #666;">Détails: ${error.message}</p>
            <p style="color: #666;">Essayez de visiter <a href="/news" target="_blank">/news</a> pour voir les données brutes.</p>
        `;
    }
});