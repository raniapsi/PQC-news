document.addEventListener("DOMContentLoaded", async () => {
    const newsList = document.getElementById("news-list");

    try {
        // Use relative URL for production compatibility
        const apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? "http://127.0.0.1:8000/news"
            : "/news";
        
        const response = await fetch(apiUrl);
        const newsData = await response.json();

        const entries = Object.entries(newsData);
        if (entries.length === 0) {
            const empty = document.createElement("p");
            empty.textContent = "Aucune donnée d'actualités disponible.";
            newsList.appendChild(empty);
            return;
        }

        entries.forEach(([category, articles]) => {
            const categoryTitle = document.createElement("h2");
            categoryTitle.textContent = category;
            newsList.appendChild(categoryTitle);

            if (!articles || articles.length === 0) {
                const empty = document.createElement("p");
                empty.textContent = "Aucun article pour ce mois.";
                newsList.appendChild(empty);
                return;
            }

            articles.forEach(article => {
                const link = document.createElement("a");
                link.href = article.url;
                link.textContent = article.title;
                link.target = "_blank";

                // Affiche le domaine source
                try {
                    const domain = new URL(article.url).hostname.replace(/^www\./, "");
                    const source = document.createElement("p");
                    source.textContent = domain;
                    newsList.appendChild(link);
                    newsList.appendChild(source);
                } catch {
                    newsList.appendChild(link);
                }
            });
        });
    } catch (error) {
        console.error("Erreur lors de la récupération des actualités :", error);
        const errorMsg = document.createElement("p");
        errorMsg.textContent = "Erreur lors du chargement des actualités.";
        errorMsg.style.color = "red";
        newsList.appendChild(errorMsg);
    }
});