document.addEventListener("DOMContentLoaded", async () => {
    const newsList = document.getElementById("news-list");
    
    // Add animated loading message with progress
    newsList.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div style="font-size: 20px; margin-bottom: 20px;">
                Chargement des actualités...
            </div>
            <div style="background: #e0e0e0; height: 30px; border-radius: 15px; overflow: hidden; max-width: 400px; margin: 0 auto;">
                <div id="progress-bar" style="background: linear-gradient(90deg, #6200ea, #9c27b0); height: 100%; width: 0%; transition: width 0.3s; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
                    <span id="progress-text">0%</span>
                </div>
            </div>
            <div id="progress-message" style="margin-top: 15px; color: #666; font-size: 14px;">
                Récupération des flux RSS...
            </div>
        </div>
    `;

    const progressBar = document.getElementById("progress-bar");
    const progressText = document.getElementById("progress-text");
    const progressMessage = document.getElementById("progress-message");

    // Simulate progress while fetching
    let progress = 0;
    const progressInterval = setInterval(() => {
        if (progress < 90) {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + "%";
            progressText.textContent = Math.round(progress) + "%";
            
            // Update message based on progress
            if (progress < 30) {
                progressMessage.textContent = " Récupération des flux RSS...";
            } else if (progress < 60) {
                progressMessage.textContent = " Analyse des articles PQC...";
            } else {
                progressMessage.textContent = " Collecte des actualités quantiques...";
            }
        }
    }, 200);

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
        
        // Complete progress
        clearInterval(progressInterval);
        progressBar.style.width = "100%";
        progressText.textContent = "100%";
        progressMessage.textContent = "Chargement terminé !";
        
        // Wait a moment to show completion
        await new Promise(resolve => setTimeout(resolve, 500));
        
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
        clearInterval(progressInterval);
        console.error("Erreur lors de la récupération des actualités :", error);
        newsList.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <p style="color: red; font-size: 20px;">Erreur lors du chargement</p>
                <p style="color: #666;">Détails: ${error.message}</p>
                <p style="color: #666;">Essayez de visiter <a href="/news" target="_blank">/news</a> pour voir les données brutes.</p>
            </div>
        `;
    }
});