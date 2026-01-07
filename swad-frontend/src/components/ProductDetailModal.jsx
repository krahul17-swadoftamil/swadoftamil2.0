import { useEffect, useState } from "react";
import {
  motion,
  AnimatePresence,
  useReducedMotion,
} from "framer-motion";

/* ================= SUPPRESS FRAMER MOTION WARNING ================= */
const originalWarn = console.warn;
console.warn = (...args) => {
  if (args[0]?.includes?.("You have Reduced Motion enabled")) {
    return; // Suppress this specific warning
  }
  originalWarn(...args);
};

import { useCart } from "../context/CartContext";
import { resolveMediaUrl } from "../utils/media";
import { ChevronDown, ChevronRight } from "lucide-react";
import { api } from "../api";

/* ================= COMPONENTS ================= */
import SnackPickerModal from "./SnackPickerModal";
import ItemCardMini from "./ItemCardMini";
import SnackCard from "./SnackCard";

/* ======================================================
   Premium ProductDetailModal — Luxury Combo Detail Experience
   Features:
   • Immersive hero section with dynamic gradients
   • Sophisticated ingredient transparency
   • Smart recommendations with micro-animations
   • Premium visual hierarchy & spacing
   • Enhanced mobile experience
   • Smooth micro-interactions
====================================================== */

export default function ProductDetailModal({
  product,
  onClose,
  isAuthenticated = false,
  onRequireAuth = () => {},
}) {
  const { addCombo, addSnack, addItem, openCheckout, total } = useCart();
  const reduceMotion = useReducedMotion();

  const [qty, setQty] = useState(1);
  const [showDetails, setShowDetails] = useState(false);
  const [showSnackPicker, setShowSnackPicker] = useState(false);
  const [addingRecommendations, setAddingRecommendations] = useState(new Set());
  const [lowStockIngredients, setLowStockIngredients] = useState(new Set());
  const [showingPortionInfo, setShowingPortionInfo] = useState(null);
  const [showingWhy, setShowingWhy] = useState(null);
  const [isImageLoaded, setIsImageLoaded] = useState(false);
  const [showAllRecommendations, setShowAllRecommendations] = useState(false);

  /* ================= ESC CLOSE ================= */
  useEffect(() => {
    const esc = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [onClose]);

  /* ================= RESET STATE ON PRODUCT CHANGE ================= */
  useEffect(() => {
    setShowDetails(false);
    setShowingWhy(null);
    setShowingPortionInfo(null);
    setIsImageLoaded(false);
    setShowAllRecommendations(false);
  }, [product?.id]);

  /* ================= FETCH LOW STOCK INGREDIENTS ================= */
  useEffect(() => {
    const fetchLowStockIngredients = async () => {
      try {
        const response = await api.get("/ingredients/low_stock/");
        const lowStockNames = new Set(response.data.results.map(ing => ing.name.toLowerCase()));
        setLowStockIngredients(lowStockNames);
      } catch (error) {
        console.warn("Failed to fetch low stock ingredients:", error);
      }
    };

    fetchLowStockIngredients();
  }, []);

  if (!product || typeof product !== 'object') {
    return (
      <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-card rounded-2xl p-6 text-center">
          <div className="text-3xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold mb-2">Product Not Available</h2>
          <p className="text-muted mb-4">This product information could not be loaded.</p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-accent text-black rounded-lg font-semibold"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  const isCombo = Array.isArray(product.items);

  /* ================= IMAGE ================= */
  const image = resolveMediaUrl(
    product.primary_image ||
      product.image ||
      (Array.isArray(product.images) ? product.images[0] : null)
  );

  /* ================= DATA ================= */
  const title = product.name || "Combo";
  const price = Math.round(Number(product.selling_price || 0));
  const serves = product.serve_persons || product.serves || null;

  /* ================= ICONS FOR WHAT YOU GET ================= */
  const getFoodIcon = (itemName) => {
    const name = (itemName || '').toLowerCase();
    if (name.includes('idli')) return '🫓';
    if (name.includes('dosa')) return '🥞';
    if (name.includes('sambar') || name.includes('rasam')) return '🍲';
    if (name.includes('chutney')) return '🥥';
    if (name.includes('murukku') || name.includes('mixture')) return '🍪';
    if (name.includes('sweet')) return '🍬';
    if (name.includes('coffee') || name.includes('tea')) return '☕';
    return '🍽️';
  };

  const getIngredientIcon = (ingredientName) => {
    const name = (ingredientName || '').toLowerCase();
    if (name.includes('rice')) return '🌾';
    if (name.includes('urad') || name.includes('dal')) return '🫘';
    if (name.includes('wheat') || name.includes('flour')) return '🌾';
    if (name.includes('oil')) return '🫒';
    if (name.includes('salt')) return '🧂';
    if (name.includes('sugar')) return '🧁';
    if (name.includes('milk')) return '🥛';
    if (name.includes('coconut')) return '🥥';
    if (name.includes('chili') || name.includes('pepper')) return '🌶️';
    if (name.includes('onion')) return '🧅';
    if (name.includes('tomato')) return '🍅';
    if (name.includes('garlic')) return '🧄';
    if (name.includes('ginger')) return '🫚';
    if (name.includes('cumin') || name.includes('jeera')) return '🫚';
    if (name.includes('turmeric')) return '🫚';
    if (name.includes('coriander')) return '🌿';
    return '🥕'; // Default vegetable icon
  };

  const getIngredientWhy = (groupTitle) => {
    const title = (groupTitle || '').toLowerCase();
    if (title.includes('sambar')) return 'Toor dal gives body & protein to sambar';
    if (title.includes('coconut chutney')) return 'Fresh coconut adds creaminess & traditional flavor';
    if (title.includes('tomato chutney')) return 'Slow-cooked tomatoes create tangy sweetness';
    if (title.includes('peanut chutney')) return 'Roasted peanuts provide nutty richness';
    if (title.includes('idli')) return 'Fermented rice & urad dal create soft, fluffy texture';
    if (title.includes('dosa')) return 'Rice & urad dal batter makes crispy exterior';
    if (title.includes('murukku') || title.includes('mixture')) return 'Lentils & spices create crunchy traditional snack';
    return 'Fresh ingredients selected for authentic South Indian taste';
  };

  const getPortionExplanation = (item, quantity, unit, allItems) => {
    const itemName = (item.display_text || '').toLowerCase();
    const qtyNum = Math.round(parseFloat(quantity));
    
    // Count idlis and dosas in the combo
    const idliCount = allItems.filter(i => 
      (i.display_text || '').toLowerCase().includes('idli')
    ).reduce((sum, i) => sum + Math.round(parseFloat(i.quantity || i.display_quantity || 0)), 0);
    
    const dosaCount = allItems.filter(i => 
      (i.display_text || '').toLowerCase().includes('dosa')
    ).reduce((sum, i) => sum + Math.round(parseFloat(i.quantity || i.display_quantity || 0)), 0);
    
    const totalMainItems = idliCount + dosaCount;
    
    if (itemName.includes('sambar')) {
      if (totalMainItems > 0) {
        return `${qtyNum} ml sambar is ideal for ${totalMainItems} ${totalMainItems === 1 ? 'idli/dosa' : 'idlis/dosas'}.`;
      }
      return `${qtyNum} ml sambar provides the perfect balance of spice and comfort.`;
    }
    
    if (itemName.includes('chutney')) {
      if (totalMainItems > 0) {
        return `${qtyNum} g ${itemName} complements ${totalMainItems} ${totalMainItems === 1 ? 'idli/dosa' : 'idlis/dosas'} perfectly.`;
      }
      return `${qtyNum} g ${itemName} adds the perfect tangy contrast.`;
    }
    
    if (itemName.includes('idli')) {
      return `${qtyNum} ${qtyNum === 1 ? 'piece' : 'pieces'} of steamed idli is a satisfying, healthy start to your day.`;
    }
    
    if (itemName.includes('dosa')) {
      return `${qtyNum} ${qtyNum === 1 ? 'dosa' : 'dosas'} delivers that perfect crispy exterior with soft interior.`;
    }
    
    return `${qtyNum} ${unit} of ${item.display_text} is thoughtfully portioned for the best experience.`;
  };

  /* ================= RECOMMENDATIONS LOGIC ================= */
  const getComplementaryRecommendations = (combo, showAll = false) => {
    try {
      const now = new Date();
      const hour = now.getHours();
      const isMorning = hour >= 6 && hour < 12;
      const isAfternoon = hour >= 12 && hour < 17;
      const isEvening = hour >= 17;

      // Time-sensitive logic: Afternoon = nothing, keep clean
      if (isAfternoon) return [];

      const recommendations = [];
      const comboName = (combo?.name || '').toLowerCase();
      const hasIdli = comboName.includes('idli') || (combo?.items && Array.isArray(combo.items) && combo.items.some(item => 
        (item.prepared_item_name || '').toLowerCase().includes('idli')
      ));
      const hasDosa = comboName.includes('dosa') || (combo?.items && Array.isArray(combo.items) && combo.items.some(item => 
        (item.prepared_item_name || '').toLowerCase().includes('dosa')
      ));
      const isFamilySize = combo?.serve_persons >= 3;

      // Helper function to check if ingredient is low stock
      const isLowStock = (ingredientName) => {
        const name = ingredientName.toLowerCase();
        return lowStockIngredients.has(name);
      };

      // Morning: Extra sambar, extra idli
      if (isMorning) {
        recommendations.push({
          id: 'extra-sambar',
          name: 'Extra Sambar',
          description: '100ml • Perfect for sharing',
          price: 25,
          icon: '🍛',
          category: 'sauce',
          ingredients: ['vegetables', 'spices'] // Generic, not coconut-specific
        });
        recommendations.push({
          id: 'extra-idli',
          name: 'Extra Idli',
          description: '2 pieces • Steamed rice cakes',
          price: 30,
          icon: '🫓',
          category: 'item',
          ingredients: ['rice', 'urad dal']
        });
      } else if (isEvening) {
        // Evening: Snacks only
        if (isFamilySize) {
          recommendations.push({
            id: 'banana-chips',
            name: 'Banana Chips',
            description: 'Handmade • Evening snack',
            price: 45,
            icon: '🍌',
            category: 'snack',
            ingredients: ['banana', 'oil']
          });
        }
        recommendations.push({
          id: 'murukku',
          name: 'Murukku',
          description: 'Crispy snack • Traditional',
          price: 35,
          icon: '🍪',
          category: 'snack',
          ingredients: ['rice flour', 'oil']
        });
      } else {
        // Kitchen load-aware recommendations
        // Base recommendations for idli combos
        if (hasIdli) {
          recommendations.push({
            id: 'extra-sambar',
            name: 'Extra Sambar',
            description: '100ml • Perfect for sharing',
            price: 25,
            icon: '🍛',
            category: 'sauce',
            ingredients: ['vegetables', 'spices']
          });

          // Prefer alternatives if coconut is low stock
          if (isLowStock('coconut')) {
            // Coconut low - prefer tomato chutney or peanut chutney
            if (!isLowStock('tomato')) {
              recommendations.push({
                id: 'extra-chutney',
                name: 'Extra Tomato Chutney',
                description: '50g • Spicy & tangy',
                price: 15,
                icon: '🍅',
                category: 'sauce',
                ingredients: ['tomato', 'spices']
              });
            } else if (!isLowStock('peanut')) {
              recommendations.push({
                id: 'peanut-chutney',
                name: 'Extra Peanut Chutney',
                description: '50g • Rich & nutty',
                price: 18,
                icon: '🥜',
                category: 'sauce',
                ingredients: ['peanut', 'spices']
              });
            }
          } else {
            // Coconut available - recommend coconut chutney
            recommendations.push({
              id: 'extra-chutney',
              name: 'Extra Coconut Chutney',
              description: '50g • Traditional recipe',
              price: 15,
              icon: '🥥',
              category: 'sauce',
              ingredients: ['coconut', 'spices']
            });
          }
        }

        // Base recommendations for dosa combos
        if (hasDosa) {
          recommendations.push({
            id: 'extra-sambar',
            name: 'Extra Sambar',
            description: '100ml • Perfect for sharing',
            price: 25,
            icon: '🍛',
            category: 'sauce',
            ingredients: ['vegetables', 'spices']
          });

          // Same logic for dosa combos - prefer alternatives if coconut low
          if (isLowStock('coconut')) {
            if (!isLowStock('tomato')) {
              recommendations.push({
                id: 'extra-chutney',
                name: 'Extra Tomato Chutney',
                description: '50g • Spicy & tangy',
                price: 15,
                icon: '🍅',
                category: 'sauce',
                ingredients: ['tomato', 'spices']
              });
            } else if (!isLowStock('peanut')) {
              recommendations.push({
                id: 'peanut-chutney',
                name: 'Extra Peanut Chutney',
                description: '50g • Rich & nutty',
                price: 18,
                icon: '🥜',
                category: 'sauce',
                ingredients: ['peanut', 'spices']
              });
            }
          } else {
            recommendations.push({
              id: 'extra-chutney',
              name: 'Extra Tomato Chutney',
              description: '50g • Spicy & tangy',
              price: 15,
              icon: '🍅',
              category: 'sauce',
              ingredients: ['tomato', 'spices']
            });
          }
        }

        // Always include one snack option if not evening
        if (!recommendations.some(r => r.category === 'snack')) {
          recommendations.push({
            id: 'murukku',
            name: 'Murukku',
            description: 'Crispy snack • Traditional',
            price: 35,
            icon: '🍪',
            category: 'snack',
            ingredients: ['rice flour', 'oil']
          });
        }

        // Add more recommendations when expanded
        if (showAll) {
          // Additional sauces
          if (!recommendations.some(r => r.id === 'extra-coconut-chutney')) {
            recommendations.push({
              id: 'extra-coconut-chutney',
              name: 'Extra Coconut Chutney',
              description: '50g • Creamy & fresh',
              price: 15,
              icon: '🥥',
              category: 'sauce',
              ingredients: ['coconut', 'spices']
            });
          }

          if (!recommendations.some(r => r.id === 'peanut-chutney')) {
            recommendations.push({
              id: 'peanut-chutney',
              name: 'Extra Peanut Chutney',
              description: '50g • Rich & nutty',
              price: 18,
              icon: '🥜',
              category: 'sauce',
              ingredients: ['peanut', 'spices']
            });
          }

          // Additional snacks
          recommendations.push({
            id: 'mixture',
            name: 'Mixture',
            description: 'Savory snack mix • Traditional',
            price: 40,
            icon: '🥜',
            category: 'snack',
            ingredients: ['lentils', 'spices']
          });

          recommendations.push({
            id: 'sweet-mixture',
            name: 'Sweet Mixture',
            description: 'Festive snack • Perfect finish',
            price: 45,
            icon: '🍬',
            category: 'snack',
            ingredients: ['sugar', 'nuts']
          });

          // Beverages
          recommendations.push({
            id: 'filter-coffee',
            name: 'South Indian Filter Coffee',
            description: '200ml • Traditional brew',
            price: 35,
            icon: '☕',
            category: 'beverage',
            ingredients: ['coffee', 'milk']
          });

          recommendations.push({
            id: 'masala-tea',
            name: 'Masala Tea',
            description: '200ml • Spiced & aromatic',
            price: 25,
            icon: '🍵',
            category: 'beverage',
            ingredients: ['tea', 'spices']
          });
        }
      }

      return showAll ? recommendations : recommendations.slice(0, 3); // Show 3 initially, all when expanded
    } catch (error) {
      console.warn('Error generating recommendations:', error);
      return [];
    }
  };

  /* ================= GROUPED INGREDIENT DISPLAY ================= */
  const getGroupedIngredients = (combo) => {
    try {
      if (!combo?.items || !Array.isArray(combo.items)) return [];

      const groups = [];
      const processedIngredients = new Set();

      // Helper to get preparation style
      const getPreparationStyle = (item) => {
        // Use Django's prepared_item_name if available
        if (item.prepared_item_name) {
          return item.prepared_item_name;
        }
        
        // Fallback to existing logic
        const name = (item.display_text || item.snack_name || '').toLowerCase();
        if (name.includes('sambar')) return 'Traditional Style';
        if (name.includes('coconut') && name.includes('chutney')) return 'Fresh Ground';
        if (name.includes('tomato') && name.includes('chutney')) return 'Slow Cooked';
        if (name.includes('peanut') && name.includes('chutney')) return 'Roasted & Ground';
        if (name.includes('idli')) return 'Steamed Rice Cakes';
        if (name.includes('dosa')) return 'Crispy Fermented';
        return 'House Special';
      };

      // Process each item in the combo
      combo.items.forEach((item) => {
        if (!item || !item.recipe || !Array.isArray(item.recipe) || item.recipe.length === 0) return;

        const itemName = item.display_text || item.snack_name || '';
        if (!itemName) return;

        const preparationStyle = getPreparationStyle(item);

        // Collect unique ingredients for this preparation
        const ingredients = [];
        item.recipe.forEach((recipeItem) => {
          if (!recipeItem || !recipeItem.ingredient_name) return;
          
          const ingredientName = recipeItem.ingredient_name;
          // Skip common repetitive ingredients like oil, water, salt
          if (!['oil', 'water', 'salt', 'water ', 'oil ', 'salt '].some(skip =>
            ingredientName.toLowerCase().includes(skip)
          )) {
            ingredients.push({
              name: ingredientName,
              icon: getIngredientIcon(ingredientName)
            });
          }
        });

        if (ingredients.length > 0) {
          groups.push({
            title: itemName,
            subtitle: preparationStyle,
            ingredients: ingredients.slice(0, 6) // Limit to 6 ingredients per group
          });
        }
      });

      return groups;
    } catch (error) {
      console.warn('Error processing grouped ingredients:', error);
      return [];
    }
  };

  const groupedIngredients = getGroupedIngredients(product);
  const recommendations = getComplementaryRecommendations(product, showAllRecommendations);
  const handleAddRecommendation = async (recommendation) => {
    // Show adding effect
    setAddingRecommendations(prev => new Set(prev).add(recommendation.id));
    
    // Create a mock item object for the recommendation
    const mockItem = {
      id: recommendation.id,
      name: recommendation.name,
      selling_price: recommendation.price,
      image: null, // No image for now
    };
    
    // Add based on category
    if (recommendation.category === 'snack') {
      addSnack(mockItem, 1);
    } else {
      addItem(mockItem, 1);
    }
    
    // Remove adding effect after a short delay
    setTimeout(() => {
      setAddingRecommendations(prev => {
        const newSet = new Set(prev);
        newSet.delete(recommendation.id);
        return newSet;
      });
    }, 1000);
  };

  /* ================= ADD ACTION ================= */
  const handleAdd = () => {
    addCombo(product, qty);
    openCheckout();
    onClose?.();
  };

  /* ================= ENHANCED MOTION ================= */
  const modalAnim = reduceMotion
    ? {}
    : {
        hidden: { opacity: 0, scale: 0.95, y: 20 },
        visible: {
          opacity: 1,
          scale: 1,
          y: 0,
          transition: {
            type: "spring",
            damping: 25,
            stiffness: 300,
            staggerChildren: 0.1
          }
        },
        exit: { opacity: 0, scale: 0.95, y: 10 }
      };

  const contentAnim = reduceMotion
    ? {}
    : {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
      };

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 bg-gradient-to-br from-black/90 via-black/80 to-black/90 backdrop-blur-xl flex items-center justify-center p-4 md:p-6 lg:p-8"
        onClick={onClose}
        variants={modalAnim}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <motion.div
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-lg md:max-w-2xl lg:max-w-4xl xl:max-w-5xl bg-gradient-to-b from-card via-card to-card/95 rounded-3xl overflow-hidden shadow-2xl border border-white/10 max-h-[90vh] md:max-h-[85vh] lg:max-h-[80vh] min-h-[600px] md:min-h-[700px] flex flex-col"
          variants={contentAnim}
        >
          {(() => {
            // Handle potential errors in data processing
            const safeGroupedIngredients = groupedIngredients || [];
            const safeProduct = product || {};
            const safePrice = price || 0;

            return (
              <>
                {/* ================= PREMIUM HERO SECTION ================= */}
                <div className="relative">
                  {/* HERO IMAGE WITH LOADING STATE */}
                  <div className="relative aspect-[4/3] md:aspect-[16/9] lg:aspect-[16/8] bg-gradient-to-br from-amber-50 to-orange-100 overflow-hidden">
                    {image ? (
                        <>
                          <motion.img
                            src={image}
                            alt={title}
                            className="w-full h-full object-cover"
                            initial={{ scale: 1.1, opacity: 0 }}
                            animate={{
                              scale: isImageLoaded ? 1 : 1.1,
                              opacity: isImageLoaded ? 1 : 0
                            }}
                            transition={{ duration: 0.6, ease: "easeOut" }}
                            onLoad={() => setIsImageLoaded(true)}
                          />
                          {!isImageLoaded && (
                            <div className="absolute inset-0 bg-gradient-to-br from-amber-50 to-orange-100 animate-pulse" />
                          )}
                        </>
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-amber-50 to-orange-100">
                          <div className="text-center">
                            <div className="text-6xl mb-2">🍽️</div>
                            <div className="text-amber-600 font-medium">Traditional Breakfast</div>
                          </div>
                        </div>
                      )}

                      {/* SOPHISTICATED GRADIENT OVERLAYS */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />
                      <div className="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-black/20" />

                      {/* CLOSE BUTTON - PREMIUM STYLE */}
                      <motion.button
                        onClick={onClose}
                        className="absolute top-6 right-6 bg-white/10 backdrop-blur-md hover:bg-white/20 text-white rounded-full w-12 h-12 flex items-center justify-center transition-all duration-300 shadow-lg border border-white/20"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </motion.button>

                      {/* EMOTIONAL BADGE */}
                      <div className="absolute top-6 left-6">
                        <motion.div
                          className="bg-white/90 backdrop-blur-md text-black px-4 py-2 rounded-full text-sm font-semibold shadow-lg border border-white/20"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.3 }}
                        >
                          ✨ Fresh Today
                        </motion.div>
                      </div>
                    </div>

                    {/* TITLE SECTION - FLOATING DESIGN */}
                    <div className="absolute bottom-0 left-0 right-0 p-6">
                      <motion.div
                        className="bg-white/95 backdrop-blur-md rounded-2xl p-6 shadow-xl border border-white/20"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                      >
                        <h1 className="text-2xl font-bold text-gray-900 mb-2">{title}</h1>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          {serves && (
                            <div className="flex items-center gap-1">
                              <span className="text-lg">👥</span>
                              <span className="font-medium">Serves {serves}</span>
                            </div>
                          )}
                          <div className="flex items-center gap-1">
                            <span className="text-lg">⭐</span>
                            <span className="font-medium">Premium Quality</span>
                          </div>
                        </div>
                      </motion.div>
                    </div>
                  </div>

                  {/* ================= PREMIUM CONTENT SECTION ================= */}
                  <div className="flex-1 overflow-y-auto overflow-x-hidden px-6 pb-6 pt-4 scrollbar-thin scrollbar-thumb-accent/20 scrollbar-track-transparent hover:scrollbar-thumb-accent/30 relative"
                       style={{
                         scrollbarWidth: 'thin',
                         scrollbarColor: 'rgba(251, 146, 60, 0.2) transparent'
                       }}>
                    {/* SCROLL INDICATOR */}
                    <div className="absolute bottom-0 left-0 right-0 h-6 bg-gradient-to-t from-white/20 to-transparent pointer-events-none z-10"></div>
                    {/* PRICE DISPLAY - PROMINENT */}
                    <motion.div
                      className="text-center mb-8"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.5 }}
                    >
                      <div className="text-4xl font-bold text-accent mb-1">₹{price}</div>
                      <div className="text-sm text-muted">per serving</div>
                    </motion.div>

                    {/* WHAT'S INCLUDED - ELEGANT CARDS */}
                    {isCombo && (
                      <motion.div
                        className="mb-8"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6 }}
                      >
                        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                          <span className="w-2 h-2 bg-accent rounded-full"></span>
                          What's in your box
                        </h3>
                        <div className="space-y-3">
                          {product.items
                            .filter((item) => item.display_text)
                            .map((item, index) => {
                              const quantity = item.display_quantity || item.quantity;
                              const unit = item.unit;
                              let quantityDisplay = '';

                              if (quantity && unit) {
                                if (unit === 'pcs') {
                                  const qtyNum = Math.round(parseFloat(quantity));
                                  quantityDisplay = `${qtyNum} pcs`;
                                } else {
                                  const qtyNum = Math.round(parseFloat(quantity));
                                  quantityDisplay = `${qtyNum} ${unit}`;
                                }
                              }

                              return (
                                <motion.div
                                  key={index}
                                  className="bg-gradient-to-r from-surface/60 to-surface/40 rounded-xl p-4 border border-white/10 shadow-sm"
                                  initial={{ opacity: 0, x: -20 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: 0.7 + index * 0.1 }}
                                  whileHover={{ scale: 1.02 }}
                                >
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                      <div className="w-12 h-12 bg-accent/10 rounded-full flex items-center justify-center text-2xl">
                                        {getFoodIcon(item.snack_name || item.display_text)}
                                      </div>
                                      <div>
                                        <div className="font-semibold text-foreground">{item.display_text}</div>
                                        <div className="text-sm text-muted">Fresh & authentic</div>
                                      </div>
                                    </div>
                                    {quantityDisplay && (
                                      <div className="flex items-center gap-2">
                                        <motion.div
                                          className="px-3 py-1 bg-accent/10 border border-accent/20 rounded-full text-sm font-semibold text-accent"
                                          whileHover={{ scale: 1.05 }}
                                        >
                                          {quantityDisplay}
                                        </motion.div>
                                        <motion.button
                                          onClick={() => setShowingPortionInfo(showingPortionInfo === index ? null : index)}
                                          className="w-6 h-6 bg-muted/20 hover:bg-muted/30 rounded-full flex items-center justify-center text-xs text-muted transition-colors"
                                          whileHover={{ scale: 1.1 }}
                                          whileTap={{ scale: 0.9 }}
                                        >
                                          ⓘ
                                        </motion.button>
                                      </div>
                                    )}
                                  </div>

                                  {/* PORTION EXPLANATION TOOLTIP */}
                                  <AnimatePresence>
                                    {showingPortionInfo === index && (
                                      <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: "auto", opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="mt-3 p-3 bg-accent/5 border border-accent/10 rounded-lg"
                                      >
                                        <p className="text-sm text-accent font-medium">
                                          {getPortionExplanation(item, quantity, unit, product.items)}
                                        </p>
                                      </motion.div>
                                    )}
                                  </AnimatePresence>
                                </motion.div>
                              );
                            })}
                        </div>
                      </motion.div>
                    )}

                    {/* SMART RECOMMENDATIONS */}
                    {recommendations.length > 0 && (
                      <motion.div
                        className="mb-8"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.8 }}
                      >
                        <h3 className="text-lg font-semibold text-foreground mb-4 flex items-center gap-2">
                          <span className="text-amber-500">✨</span>
                          Perfect Pairings
                        </h3>
                        <div className="grid grid-cols-1 gap-3">
                          {recommendations.slice(0, 3).map((rec, index) => {
                            const isAdding = addingRecommendations.has(rec.id);
                            return (
                              <motion.div
                                key={rec.id}
                                className="bg-gradient-to-r from-amber-50/50 to-orange-50/50 rounded-xl p-4 border border-amber-100/50 shadow-sm"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: 0.9 + index * 0.1 }}
                                whileHover={{ scale: 1.02 }}
                              >
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-3">
                                    <div className="text-2xl">{rec.icon}</div>
                                    <div>
                                      <div className="font-semibold text-foreground">{rec.name}</div>
                                      <div className="text-sm text-muted">{rec.description}</div>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    <div className="text-lg font-bold text-accent">₹{rec.price}</div>
                                    <motion.button
                                      onClick={() => handleAddRecommendation(rec)}
                                      disabled={isAdding}
                                      className="px-4 py-2 bg-accent/10 hover:bg-accent/20 text-accent text-sm font-semibold rounded-lg border border-accent/20 transition-all duration-200 disabled:opacity-50"
                                      whileHover={{ scale: 1.05 }}
                                      whileTap={{ scale: 0.95 }}
                                    >
                                      {isAdding ? (
                                        <div className="flex items-center gap-2">
                                          <div className="w-3 h-3 border border-accent/30 border-t-accent rounded-full animate-spin"></div>
                                          Adding...
                                        </div>
                                      ) : (
                                        '+ Add'
                                      )}
                                    </motion.button>
                                  </div>
                                </div>
                              </motion.div>
                            );
                          })}

                          {/* Expandable additional recommendations */}
                          <AnimatePresence>
                            {showAllRecommendations && recommendations.length > 3 && (
                              <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.3, ease: "easeInOut" }}
                                className="overflow-hidden"
                              >
                                {recommendations.slice(3).map((rec, index) => {
                                  const isAdding = addingRecommendations.has(rec.id);
                                  return (
                                    <motion.div
                                      key={rec.id}
                                      className="bg-gradient-to-r from-amber-50/50 to-orange-50/50 rounded-xl p-4 border border-amber-100/50 shadow-sm mb-3"
                                      initial={{ opacity: 0, y: 20 }}
                                      animate={{ opacity: 1, y: 0 }}
                                      transition={{ delay: index * 0.1 }}
                                      whileHover={{ scale: 1.02 }}
                                    >
                                      <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                          <div className="text-2xl">{rec.icon}</div>
                                          <div>
                                            <div className="font-semibold text-foreground">{rec.name}</div>
                                            <div className="text-sm text-muted">{rec.description}</div>
                                          </div>
                                        </div>
                                        <div className="flex items-center gap-3">
                                          <div className="text-lg font-bold text-accent">₹{rec.price}</div>
                                          <motion.button
                                            onClick={() => handleAddRecommendation(rec)}
                                            disabled={isAdding}
                                            className="px-4 py-2 bg-accent/10 hover:bg-accent/20 text-accent text-sm font-semibold rounded-lg border border-accent/20 transition-all duration-200 disabled:opacity-50"
                                            whileHover={{ scale: 1.05 }}
                                            whileTap={{ scale: 0.95 }}
                                          >
                                            {isAdding ? (
                                              <div className="flex items-center gap-2">
                                                <div className="w-3 h-3 border border-accent/30 border-t-accent rounded-full animate-spin"></div>
                                                Adding...
                                              </div>
                                            ) : (
                                              '+ Add'
                                            )}
                                          </motion.button>
                                        </div>
                                      </div>
                                    </motion.div>
                                  );
                                })}
                              </motion.div>
                            )}
                          </AnimatePresence>

                          {/* Expand/Collapse Button */}
                          {recommendations.length > 3 && (
                            <motion.button
                              onClick={() => setShowAllRecommendations(!showAllRecommendations)}
                              className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-accent/10 to-accent/5 hover:from-accent/20 hover:to-accent/10 text-accent font-semibold rounded-xl border border-accent/20 transition-all duration-300 flex items-center justify-center gap-2"
                              whileHover={{ scale: 1.02 }}
                              whileTap={{ scale: 0.98 }}
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              transition={{ delay: 1.2 }}
                            >
                              <motion.span
                                animate={{ rotate: showAllRecommendations ? 180 : 0 }}
                                transition={{ duration: 0.2 }}
                              >
                                ▼
                              </motion.span>
                              {showAllRecommendations ? 'Show fewer options' : `View ${recommendations.length - 3} more add-ons`}
                            </motion.button>
                          )}
                        </div>
                      </motion.div>
                    )}

                    {/* INGREDIENT TRANSPARENCY SECTION */}
                    <motion.div
                      className="mb-8"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.0 }}
                    >
                      <motion.button
                        onClick={() => setShowDetails(!showDetails)}
                        className="w-full bg-gradient-to-r from-surface/60 to-surface/40 hover:from-surface/80 hover:to-surface/60 rounded-xl p-4 border border-white/10 shadow-sm transition-all duration-300"
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-accent/10 rounded-full flex items-center justify-center">
                              <span className="text-lg">🌿</span>
                            </div>
                            <div className="text-left">
                              <div className="font-semibold text-foreground">See what's inside</div>
                              <div className="text-sm text-muted">Fresh ingredients & traditional recipes</div>
                            </div>
                          </div>
                          <motion.div
                            animate={{ rotate: showDetails ? 180 : 0 }}
                            transition={{ duration: 0.3 }}
                          >
                            <svg className="w-5 h-5 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                            </svg>
                          </motion.div>
                        </div>
                      </motion.button>

                      {/* COLLAPSIBLE INGREDIENT DETAILS */}
                      <AnimatePresence>
                        {showDetails && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.4, ease: "easeInOut" }}
                            className="mt-4 overflow-hidden"
                          >
                            <div className="bg-gradient-to-b from-surface/40 to-surface/20 rounded-xl p-6 border border-white/10">
                              {/* DESCRIPTION */}
                              {product.description && (
                                <div className="mb-6">
                                  <h4 className="font-semibold text-foreground mb-2">About this combo</h4>
                                  <p className="text-sm text-muted leading-relaxed">{product.description}</p>
                                </div>
                              )}

                              {/* INGREDIENT BREAKDOWN */}
                              {groupedIngredients.length > 0 ? (
                                <div>
                                  <h4 className="font-semibold text-foreground mb-4">Made with fresh ingredients</h4>

                                  {isAuthenticated ? (
                                    // FULL INGREDIENT TRANSPARENCY - AUTHENTICATED USERS
                                    <div className="space-y-4">
                                      {groupedIngredients.map((group, index) => (
                                        <motion.div
                                          key={index}
                                          className="bg-white/50 rounded-lg p-4 border border-white/20"
                                          initial={{ opacity: 0, y: 10 }}
                                          animate={{ opacity: 1, y: 0 }}
                                          transition={{ delay: index * 0.1 }}
                                        >
                                          <div className="flex items-center justify-between mb-3">
                                            <div>
                                              <div className="font-semibold text-accent">{group.title}</div>
                                              <div className="text-sm text-muted">{group.subtitle}</div>
                                            </div>
                                            <motion.button
                                              onClick={() => setShowingWhy(showingWhy === index ? null : index)}
                                              className="w-8 h-8 bg-accent/10 hover:bg-accent/20 rounded-full flex items-center justify-center text-accent transition-colors"
                                              whileHover={{ scale: 1.1 }}
                                              whileTap={{ scale: 0.9 }}
                                            >
                                              ⓘ
                                            </motion.button>
                                          </div>

                                          {/* WHY EXPLANATION */}
                                          <AnimatePresence>
                                            {showingWhy === index && (
                                              <motion.div
                                                initial={{ height: 0, opacity: 0 }}
                                                animate={{ height: "auto", opacity: 1 }}
                                                exit={{ height: 0, opacity: 0 }}
                                                className="mb-3 p-3 bg-accent/10 border border-accent/20 rounded-md"
                                              >
                                                <p className="text-sm text-accent font-medium">
                                                  {getIngredientWhy(group.title)}
                                                </p>
                                              </motion.div>
                                            )}
                                          </AnimatePresence>

                                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                                            {group.ingredients.map((ingredient, ingIndex) => (
                                              <motion.div
                                                key={ingIndex}
                                                className="flex items-center gap-2 text-sm bg-white/30 rounded-lg p-2"
                                                initial={{ opacity: 0, scale: 0.9 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                transition={{ delay: (index * 0.1) + (ingIndex * 0.05) }}
                                              >
                                                <span className="text-base">{ingredient.icon}</span>
                                                <span className="text-muted">{ingredient.name}</span>
                                              </motion.div>
                                            ))}
                                          </div>
                                        </motion.div>
                                      ))}
                                    </div>
                                  ) : (
                                    // INGREDIENT TRANSPARENCY GATE - UNAUTHENTICATED USERS
                                    <div className="text-center space-y-4 py-6">
                                      <div className="text-4xl mb-4">🔍</div>
                                      <div className="space-y-2">
                                        <h4 className="font-semibold text-foreground">
                                          Unlock ingredient transparency
                                        </h4>
                                        <p className="text-sm text-muted">
                                          See exactly what's in your breakfast - from farm to plate
                                        </p>
                                      </div>
                                      <motion.button
                                        onClick={onRequireAuth}
                                        className="w-full py-3 px-6 rounded-xl text-sm font-semibold bg-accent text-black hover:bg-accent/90 transition-all duration-200 shadow-lg"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                      >
                                        Continue with Google
                                      </motion.button>
                                    </div>
                                  )}
                                </div>
                              ) : (
                                // FALLBACK WHEN NO RECIPE DATA AVAILABLE
                                <div className="text-center space-y-4 py-6">
                                  <div className="text-4xl mb-4">👨‍🍳</div>
                                  <div className="space-y-2">
                                    <h4 className="font-semibold text-foreground">
                                      Traditional South Indian Recipe
                                    </h4>
                                    <p className="text-sm text-muted">
                                      Each item is carefully prepared using time-honored techniques and the finest fresh ingredients from local markets.
                                    </p>
                                  </div>
                                </div>
                              )}

                              {/* ASSURANCES */}
                              <div className="flex flex-wrap gap-3 mt-6 pt-4 border-t border-white/10">
                                <div className="flex items-center gap-2 text-xs text-muted bg-white/20 rounded-full px-3 py-1">
                                  <span className="text-green-500">✓</span>
                                  <span>Fresh today</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-muted bg-white/20 rounded-full px-3 py-1">
                                  <span className="text-green-500">✓</span>
                                  <span>Exact quantity</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-muted bg-white/20 rounded-full px-3 py-1">
                                  <span className="text-green-500">✓</span>
                                  <span>No substitutions</span>
                                </div>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>

                    {/* QUANTITY CONTROLS & CART TOTAL */}
                    <motion.div
                      className="space-y-4"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 1.1 }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3 bg-surface/60 rounded-xl p-2 border border-white/10">
                          <motion.button
                            onClick={() => setQty((q) => Math.max(1, q - 1))}
                            className="w-10 h-10 rounded-lg hover:bg-white/10 flex items-center justify-center text-lg font-semibold transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            −
                          </motion.button>
                          <span className="w-12 text-center font-bold text-lg">{qty}</span>
                          <motion.button
                            onClick={() => setQty((q) => q + 1)}
                            className="w-10 h-10 rounded-lg hover:bg-white/10 flex items-center justify-center text-lg font-semibold transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                          >
                            +
                          </motion.button>
                        </div>

                        {total > 0 && (
                          <div className="bg-accent/10 border border-accent/20 rounded-xl px-4 py-2">
                            <div className="text-sm text-muted">Cart total</div>
                            <div className="font-bold text-accent">₹{total}</div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  </div>

                  {/* ================= STICKY BOTTOM CTA ================= */}
                  <motion.div
                    className="flex-shrink-0 sticky bottom-0 bg-gradient-to-t from-white via-white/95 to-white/90 backdrop-blur-md border-t border-white/20 p-6"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1.2 }}
                  >
                    <motion.button
                      onClick={handleAdd}
                      className="w-full bg-gradient-to-r from-accent to-accent/90 hover:from-accent/90 hover:to-accent text-black font-bold py-4 px-6 rounded-xl text-lg shadow-lg transition-all duration-300"
                      whileHover={{ scale: 1.02, y: -1 }}
                      whileTap={{ scale: 0.98 }}
                    >
                      <div className="flex items-center justify-center gap-2">
                        <span>Add to Cart</span>
                        <span className="text-xl">•</span>
                        <span>₹{price * qty}</span>
                      </div>
                    </motion.button>
                  </motion.div>
                </>
              );
          })()}
        </motion.div>
      </motion.div>

      {/* ================= SNACK PICKER MODAL ================= */}
      <SnackPickerModal
        open={showSnackPicker}
        onClose={() => setShowSnackPicker(false)}
      />
    </AnimatePresence>
  );
}
