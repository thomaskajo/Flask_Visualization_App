// 卡片数据
const cards = [
    { icon: 'bi-leaf', title: 'Dashboard', text: 'Monitor environmental impact and sustainability metrics', redirect:'dashboard' },
    // { icon: 'bi-people', title: 'Social', text: 'Track social responsibility and community impact' },
    // { icon: 'bi-shield-check', title: 'Governance', text: 'Manage corporate governance and compliance' },
    { icon: 'bi-graph-up', title: 'Performance Metrics', text: 'View key performance indicators and trends', redirect:'analytics' },
    { icon: 'bi-file-earmark-text', title: 'Reports', text: 'Generate and manage reports and disclosures', redirect:'personal-collection' }
];

// 获取卡片容器
const cardContainer = document.getElementById('cardContainer');

// 循环输出卡片
cards.forEach((card, index) => {
    const colClass = index < 3 ? 'col-md-4' : 'col-md-6'; // 前三个卡片使用4列，后两个使用6列
    const cardHTML = `
        <div class="${colClass}">
            <div class="card h-100">
                <div class="card-body text-center" style="cursor: pointer;" onclick="window.location.href='${card.redirect}';">
                    <i class="bi ${card.icon} card-icon"></i>
                    <h5 class="card-title">${card.title}</h5>
                    <p class="card-text">${card.text}</p>
                </div>
            </div>
        </div>
    `;
    cardContainer.innerHTML += cardHTML; // 将卡片HTML添加到容器中
});