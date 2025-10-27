-- 006_add_color_columns.sql

-- Add color column to category_options
ALTER TABLE vinted.category_options ADD COLUMN color VARCHAR(7);

-- Add color column to platform_options
ALTER TABLE vinted.platform_options ADD COLUMN color VARCHAR(7);

-- Add color column to condition_options
ALTER TABLE vinted.condition_options ADD COLUMN color VARCHAR(7);

-- Add color column to source_options
ALTER TABLE vinted.source_options ADD COLUMN color VARCHAR(7);

-- Populate default colors for category_options
UPDATE vinted.category_options SET color = '#FF5733' WHERE id = 3026; -- Video Games
UPDATE vinted.category_options SET color = '#33FF57' WHERE id = 1953; -- Computers
UPDATE vinted.category_options SET color = '#3357FF' WHERE id = 184;  -- Mobile Phones
UPDATE vinted.category_options SET color = '#FF33F0' WHERE id = 188;  -- Tablets
UPDATE vinted.category_options SET color = '#F0FF33' WHERE id = 3013; -- Consoles
UPDATE vinted.category_options SET color = '#FF6600' WHERE id = 3055; -- Accessories
UPDATE vinted.category_options SET color = '#00FFFF' WHERE id = 5;    -- Books & Entertainment
UPDATE vinted.category_options SET color = '#8A2BE2' WHERE id = 1243; -- Home & Living
UPDATE vinted.category_options SET color = '#A52A2A' WHERE id = 1261; -- Collectibles
UPDATE vinted.category_options SET color = '#DE3163' WHERE id = 16;   -- Women's Clothing
UPDATE vinted.category_options SET color = '#40E0D0' WHERE id = 18;   -- Men's Clothing
UPDATE vinted.category_options SET color = '#6495ED' WHERE id = 12;   -- Kids & Baby
UPDATE vinted.category_options SET color = '#CCCCFF' WHERE id = 1;    -- Women
UPDATE vinted.category_options SET color = '#FFD700' WHERE id = 2;    -- Men
UPDATE vinted.category_options SET color = '#DA70D6' WHERE id = 4;    -- Kids
UPDATE vinted.category_options SET color = '#ADFF2F' WHERE id = 2994; -- Electronics

-- Populate default colors for platform_options (using some reasonable defaults)
UPDATE vinted.platform_options SET color = '#00B289' WHERE name = 'Vinted';
UPDATE vinted.platform_options SET color = '#FF0066' WHERE name = 'Depop';
UPDATE vinted.platform_options SET color = '#E53238' WHERE name = 'Ebay';

-- Populate default colors for condition_options
UPDATE vinted.condition_options SET color = '#00CC66' WHERE id = 2;  -- New
UPDATE vinted.condition_options SET color = '#66FF99' WHERE id = 3;  -- Like new
UPDATE vinted.condition_options SET color = '#FFCC00' WHERE id = 7;  -- Fair
UPDATE vinted.condition_options SET color = '#FF9933' WHERE id = 8;  -- Poor
UPDATE vinted.condition_options SET color = '#FF6666' WHERE id = 9;  -- Needs repair
UPDATE vinted.condition_options SET color = '#808080' WHERE id = 10; -- Unknown
UPDATE vinted.condition_options SET color = '#FFDAB9' WHERE id = 12; -- Uspokojivé
UPDATE vinted.condition_options SET color = '#ADD8E6' WHERE id = 13; -- Nový s visačkou
UPDATE vinted.condition_options SET color = '#90EE90' WHERE id = 14; -- Nový bez visačky
UPDATE vinted.condition_options SET color = '#DDA0DD' WHERE id = 15; -- Nové s visačkou
UPDATE vinted.condition_options SET color = '#F0E68C' WHERE id = 16; -- Veľmi dobré
UPDATE vinted.condition_options SET color = '#B0E0E6' WHERE id = 17; -- Velmi dobrý
UPDATE vinted.condition_options SET color = '#FFE4B5' WHERE id = 18; -- Dobré
UPDATE vinted.condition_options SET color = '#98FB98' WHERE id = 19; -- Nové bez visačky
UPDATE vinted.condition_options SET color = '#FFA07A' WHERE id = 6;  -- Satisfactory
UPDATE vinted.condition_options SET color = '#20B2AA' WHERE id = 1;  -- New with tags
UPDATE vinted.condition_options SET color = '#7FFF00' WHERE id = 4;  -- Very good
UPDATE vinted.condition_options SET color = '#FFD700' WHERE id = 5;  -- Good

-- Populate default colors for source_options (using some reasonable defaults)
UPDATE vinted.source_options SET color = '#00B289' WHERE code = 'vinted';
UPDATE vinted.source_options SET color = '#8A2BE2' WHERE code = 'bazos';
UPDATE vinted.source_options SET color = '#808080' WHERE code = 'manual';
