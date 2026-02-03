/**
 * CitySelector Component
 * 统一的城市选择器组件，用于历史查询和天气实况
 * 支持模式: 'grid' (传统平铺), 'tags' (紧凑标签输入)
 */
class CitySelector {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = {
            mode: 'single', // 'single' | 'multi'
            renderMode: 'grid', // 'grid' | 'tags'
            showSearch: true,
            placeholder: '搜索或选择城市...',
            onSelect: null, // callback(cityId | [cityIds])
            ...options
        };
        
        this.cities = [];
        this.selectedIds = new Set();
        this.searchTerm = '';
        this.isDropdownOpen = false;
        
        // Bind methods
        this.handleClickOutside = this.handleClickOutside.bind(this);
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.warn(`CitySelector container #${this.containerId} not found`);
            return;
        }
        
        // Add global click listener for dropdown closing
        document.addEventListener('click', this.handleClickOutside);
        
        this.renderStructure();
    }
    
    dispose() {
        document.removeEventListener('click', this.handleClickOutside);
    }
    
    handleClickOutside(event) {
        if (this.options.renderMode !== 'tags') return;
        if (!this.container.contains(event.target)) {
            this.closeDropdown();
        }
    }
    
    setCities(cities) {
        this.cities = cities || [];
        this.render();
    }
    
    setSelected(ids) {
        if (Array.isArray(ids)) {
            this.selectedIds = new Set(ids);
        } else {
            this.selectedIds = new Set([ids] || []);
        }
        // If single mode and passed multiple, take first
        if (this.options.mode === 'single' && this.selectedIds.size > 1) {
             const first = Array.from(this.selectedIds)[0];
             this.selectedIds = new Set([first]);
        }
        this.render();
    }
    
    renderStructure() {
        this.container.innerHTML = '';
        // Structure depends on renderMode, will be handled in render()
        this.render();
    }
    
    render() {
        if (this.options.renderMode === 'tags') {
            this.renderTagsMode();
        } else {
            this.renderGridMode();
        }
    }
    
    // --- Grid Mode (Legacy) ---
    renderGridMode() {
        this.container.className = 'city-selector-grid-wrapper';
        this.container.innerHTML = '';
        
        // Search Input
        if (this.options.showSearch) {
            const searchContainer = document.createElement('div');
            searchContainer.className = 'city-search-box mb-2';
            searchContainer.innerHTML = `
                <input type="text" class="form-control form-control-sm" placeholder="搜索城市..." value="${this.searchTerm}">
            `;
            const input = searchContainer.querySelector('input');
            input.oninput = (e) => {
                this.searchTerm = e.target.value.toLowerCase();
                this.renderGridList(listContainer);
                // Keep focus
                setTimeout(()=>input.focus(), 0);
            };
            this.container.appendChild(searchContainer);
        }
        
        // List
        const listContainer = document.createElement('div');
        listContainer.className = 'city-selector-grid';
        this.container.appendChild(listContainer);
        this.renderGridList(listContainer);
    }
    
    renderGridList(container) {
        container.innerHTML = '';
        const filtered = this.filterCities(this.searchTerm);
        
        if (filtered.length === 0) {
            container.innerHTML = '<div class="text-gray-500 text-xs p-2">未找到匹配城市</div>';
            return;
        }
        
        filtered.forEach(city => {
            const chip = document.createElement('div');
            chip.className = `city-chip ${this.selectedIds.has(city.id) ? 'active' : ''}`;
            chip.textContent = city.name;
            chip.onclick = () => this.handleSelect(city.id);
            container.appendChild(chip);
        });
    }

    // --- Tags Mode (New Compact) ---
    renderTagsMode() {
        // Container looks like an input box
        this.container.className = 'city-selector-tags-wrapper';
        this.container.innerHTML = '';
        
        // 1. The Input Area (Tags + Input)
        const inputBox = document.createElement('div');
        inputBox.className = 'city-tags-input-container form-control';
        inputBox.onclick = () => {
             this.openDropdown();
             inputBox.querySelector('input')?.focus();
        };

        // Render Selected Tags
        this.selectedIds.forEach(id => {
            const city = this.cities.find(c => c.id === id);
            if (!city) return;
            
            const tag = document.createElement('span');
            tag.className = 'city-tag';
            tag.innerHTML = `
                ${city.name}
                <span class="city-tag-remove" data-id="${id}">&times;</span>
            `;
            // Handle remove
            tag.querySelector('.city-tag-remove').onclick = (e) => {
                e.stopPropagation();
                this.handleSelect(id); // Toggle off
            };
            inputBox.appendChild(tag);
        });
        
        // The actual typing input
        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'city-tags-entry';
        input.placeholder = this.selectedIds.size > 0 ? '' : this.options.placeholder;
        input.value = this.searchTerm;
        input.oninput = (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            this.openDropdown();
            this.renderDropdownList();
        };
        input.onfocus = () => this.openDropdown();
        inputBox.appendChild(input);
        
        this.container.appendChild(inputBox);
        
        // 2. The Dropdown (Absolute)
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'city-dropdown-list';
        this.dropdown.style.display = 'none'; // Hidden by default
        this.container.appendChild(this.dropdown);
        
        if (this.isDropdownOpen) {
            this.dropdown.style.display = 'block';
            this.renderDropdownList();
        }
    }
    
    renderDropdownList() {
        if (!this.dropdown) return;
        this.dropdown.innerHTML = '';
        
        const filtered = this.filterCities(this.searchTerm);
        
        if (filtered.length === 0) {
            this.dropdown.innerHTML = '<div class="p-3 text-muted text-sm">无匹配城市</div>';
            return;
        }
        
        filtered.forEach(city => {
            const item = document.createElement('div');
            const isSelected = this.selectedIds.has(city.id);
            item.className = `city-dropdown-item ${isSelected ? 'selected' : ''}`;
            item.textContent = city.name;
            item.onclick = (e) => {
                e.stopPropagation();
                this.handleSelect(city.id);
                this.searchTerm = ''; // Clear search on select
                if (this.options.mode === 'single') {
                    this.closeDropdown();
                } else {
                    // Keep open for multi
                    // Focus back to input
                    const input = this.container.querySelector('input.city-tags-entry');
                    if (input) {
                        input.value = '';
                        input.focus();
                    }
                }
            };
            this.dropdown.appendChild(item);
        });
    }
    
    openDropdown() {
        this.isDropdownOpen = true;
        if (this.dropdown) {
            this.dropdown.style.display = 'block';
            this.renderDropdownList();
        }
    }
    
    closeDropdown() {
        this.isDropdownOpen = false;
        if (this.dropdown) {
            this.dropdown.style.display = 'none';
        }
    }

    filterCities(term) {
        return this.cities.filter(c => 
            c.name.toLowerCase().includes(term) || 
            (c.region && c.region.toLowerCase().includes(term))
        );
    }
    
    handleSelect(cityId) {
        if (this.options.mode === 'single') {
            this.selectedIds.clear();
            this.selectedIds.add(cityId);
        } else {
            if (this.selectedIds.has(cityId)) {
                this.selectedIds.delete(cityId);
            } else {
                this.selectedIds.add(cityId);
            }
        }
        
        this.render();
        
        if (this.options.onSelect) {
            const result = this.options.mode === 'single' 
                ? Array.from(this.selectedIds)[0] 
                : Array.from(this.selectedIds);
            this.options.onSelect(result);
        }
    }

    setOptions(newOptions) {
        // If switching from multi to single, clear or take first
        if (newOptions.mode === 'single' && this.options.mode === 'multi') {
            if (this.selectedIds.size > 1) {
                const first = Array.from(this.selectedIds)[0];
                this.selectedIds = new Set([first]);
            }
        }
        this.options = { ...this.options, ...newOptions };
        this.render();
    }
}
