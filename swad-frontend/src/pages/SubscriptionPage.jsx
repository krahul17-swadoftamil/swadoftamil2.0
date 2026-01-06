import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { api } from '../api';

const SubscriptionPage = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    delivery_address: '',
    delivery_instructions: '',
    start_date: '',
    custom_days: [],
    billing_cycle_days: 30,
  });

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await api.get('/subscription-plans/');
      setPlans(response.data);
    } catch (error) {
      console.error('Error fetching plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan);
    setFormData(prev => ({
      ...prev,
      billing_cycle_days: plan.plan_type === 'daily' ? 30 : plan.plan_type === 'weekly' ? 7 : 30,
    }));
    setShowForm(true);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCustomDaysChange = (day) => {
    setFormData(prev => ({
      ...prev,
      custom_days: prev.custom_days.includes(day)
        ? prev.custom_days.filter(d => d !== day)
        : [...prev.custom_days, day],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const subscriptionData = {
        ...formData,
        plan: selectedPlan.id,
        start_date: formData.start_date || new Date().toISOString().split('T')[0],
      };

      const response = await api.post('/subscriptions/', subscriptionData);
      alert('Subscription created successfully!');
      setShowForm(false);
      setSelectedPlan(null);
      setFormData({
        customer_name: '',
        customer_email: '',
        customer_phone: '',
        delivery_address: '',
        delivery_instructions: '',
        start_date: '',
        custom_days: [],
        billing_cycle_days: 30,
      });
    } catch (error) {
      console.error('Error creating subscription:', error);
      alert('Error creating subscription. Please try again.');
    }
  };

  const getDiscountedPrice = (plan, cycleDays) => {
    if (cycleDays >= 30 && plan.plan_type === 'daily') {
      const discount = plan.base_price * (plan.monthly_discount_percent / 100);
      return plan.base_price - discount;
    }
    return plan.base_price;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-red-50 py-12 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Swad of Tamil Subscriptions
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Never miss your favorite South Indian breakfast. Choose from our flexible subscription plans.
          </p>
        </motion.div>

        {!showForm ? (
          /* Plans Grid */
          <div className="grid md:grid-cols-3 gap-8 mb-12">
            {plans.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-2xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
              >
                <div className="bg-gradient-to-r from-orange-500 to-red-500 p-6 text-white">
                  <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                  <p className="text-orange-100">{plan.description}</p>
                </div>

                <div className="p-6">
                  <div className="text-center mb-6">
                    <div className="text-3xl font-bold text-gray-900 mb-2">
                      ₹{getDiscountedPrice(plan, 30)}
                      <span className="text-lg text-gray-500">/month</span>
                    </div>
                    {plan.monthly_discount_percent > 0 && plan.plan_type === 'daily' && (
                      <div className="text-sm text-green-600">
                        {plan.monthly_discount_percent}% off monthly billing
                      </div>
                    )}
                  </div>

                  <div className="space-y-3 mb-6">
                    <div className="flex items-center text-gray-600">
                      <span className="w-2 h-2 bg-orange-500 rounded-full mr-3"></span>
                      {plan.plan_type === 'daily' && 'Delivered every day'}
                      {plan.plan_type === 'weekly' && 'Delivered once per week'}
                      {plan.plan_type === 'custom' && 'Choose your delivery days'}
                    </div>
                    <div className="flex items-center text-gray-600">
                      <span className="w-2 h-2 bg-orange-500 rounded-full mr-3"></span>
                      Fresh, authentic South Indian cuisine
                    </div>
                    <div className="flex items-center text-gray-600">
                      <span className="w-2 h-2 bg-orange-500 rounded-full mr-3"></span>
                      Pause or cancel anytime
                    </div>
                  </div>

                  <button
                    onClick={() => handlePlanSelect(plan)}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
                  >
                    Choose Plan
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          /* Subscription Form */
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-2xl mx-auto bg-white rounded-2xl shadow-lg p-8"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Subscribe to {selectedPlan?.name}
              </h2>
              <button
                onClick={() => setShowForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Customer Details */}
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    name="customer_name"
                    value={formData.customer_name}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    name="customer_phone"
                    value={formData.customer_phone}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email Address *
                </label>
                <input
                  type="email"
                  name="customer_email"
                  value={formData.customer_email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>

              {/* Delivery Details */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Delivery Address *
                </label>
                <textarea
                  name="delivery_address"
                  value={formData.delivery_address}
                  onChange={handleInputChange}
                  required
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Enter your complete delivery address"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Delivery Instructions
                </label>
                <textarea
                  name="delivery_instructions"
                  value={formData.delivery_instructions}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Any special instructions for delivery"
                />
              </div>

              {/* Start Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date *
                </label>
                <input
                  type="date"
                  name="start_date"
                  value={formData.start_date}
                  onChange={handleInputChange}
                  min={new Date().toISOString().split('T')[0]}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                />
              </div>

              {/* Custom Days for Custom Plan */}
              {selectedPlan?.plan_type === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Delivery Days *
                  </label>
                  <div className="grid grid-cols-7 gap-2">
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day, index) => (
                      <button
                        key={day}
                        type="button"
                        onClick={() => handleCustomDaysChange(index)}
                        className={`py-2 px-3 text-sm font-medium rounded-lg border transition-colors ${
                          formData.custom_days.includes(index)
                            ? 'bg-orange-500 text-white border-orange-500'
                            : 'bg-white text-gray-700 border-gray-300 hover:border-orange-300'
                        }`}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Billing Summary */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h3 className="font-semibold text-gray-900 mb-2">Billing Summary</h3>
                <div className="space-y-1 text-sm text-gray-600">
                  <div>Plan: {selectedPlan?.name}</div>
                  <div>Base Price: ₹{selectedPlan?.base_price}</div>
                  <div>Billing Cycle: {formData.billing_cycle_days} days</div>
                  <div className="font-semibold text-gray-900">
                    Total: ₹{getDiscountedPrice(selectedPlan, formData.billing_cycle_days)} per cycle
                  </div>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                className="w-full bg-orange-500 hover:bg-orange-600 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                Create Subscription
              </button>
            </form>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionPage;