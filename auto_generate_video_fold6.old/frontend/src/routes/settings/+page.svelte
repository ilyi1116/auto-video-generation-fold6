<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast';
  import { authStore } from '$lib/stores/auth';
  import { LoadingSpinner } from '$lib/components/ui';
  
  // Import refactored components
  import ProfileSettings from '$lib/components/settings/ProfileSettings.svelte';
  import SecuritySettings from '$lib/components/settings/SecuritySettings.svelte';
  import NotificationSettings from '$lib/components/settings/NotificationSettings.svelte';
  import EntrepreneurModeSettings from '$lib/components/settings/EntrepreneurModeSettings.svelte';
  
  import { 
    User, 
    Shield, 
    Bell, 
    Eye, 
    Palette, 
    CreditCard,
    Settings as SettingsIcon,
    Zap
  } from 'lucide-svelte';

  let isLoading = true;
  let activeTab = 'profile';
  let isSaving = false;
  
  let settingsData = {
    profile: {},
    notifications: {},
    privacy: {},
    appearance: {},
    billing: {},
    entrepreneurMode: {}
  };

  const tabs = [
    {
      id: 'profile',
      name: 'Profile',
      icon: User,
      description: 'Manage your account information'
    },
    {
      id: 'entrepreneurMode',
      name: 'Entrepreneur Mode',
      icon: Zap,
      description: 'Automated content creation for profit'
    },
    {
      id: 'notifications',
      name: 'Notifications',
      icon: Bell,
      description: 'Control how you receive updates'
    },
    {
      id: 'privacy',
      name: 'Privacy',
      icon: Eye,
      description: 'Manage your privacy settings'
    },
    {
      id: 'appearance',
      name: 'Appearance',
      icon: Palette,
      description: 'Customize your experience'
    },
    {
      id: 'billing',
      name: 'Billing',
      icon: CreditCard,
      description: 'Manage subscription and payments'
    },
    {
      id: 'security',
      name: 'Security',
      icon: Shield,
      description: 'Password and security settings'
    }
  ];

  onMount(async () => {
    await loadSettingsData();
  });

  async function loadSettingsData() {
    try {
      isLoading = true;
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      settingsData = {
        profile: {
          first_name: 'John',
          last_name: 'Doe',
          email: 'john.doe@example.com',
          bio: 'Creative content creator focused on automation and AI.',
          website: 'https://johndoe.com',
          location: 'San Francisco, CA',
          avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face'
        },
        notifications: {
          email: {
            projectUpdates: true,
            weeklyReports: true,
            securityAlerts: true,
            marketing: false,
            newFeatures: true
          },
          push: {
            projectComplete: true,
            mentions: true,
            newMessages: false,
            systemAlerts: true
          },
          sms: {
            securityAlerts: false,
            criticalAlerts: false
          }
        },
        privacy: {
          profileVisibility: 'public',
          showActivity: true,
          allowMessages: true,
          analyticsSharing: false
        },
        appearance: {
          theme: 'system',
          language: 'en',
          timezone: 'America/Los_Angeles',
          compactMode: false
        },
        billing: {
          plan: 'Pro',
          billingCycle: 'monthly',
          nextBilling: '2024-02-15',
          paymentMethod: '**** 4242'
        },
        entrepreneurMode: {
          enabled: false,
          autoTrendsFetch: true,
          dailyVideoCount: 3,
          operatingHours: {
            start: '09:00',
            end: '18:00',
            timezone: 'Asia/Taipei'
          },
          contentPreferences: {
            categories: ['technology', 'entertainment', 'lifestyle'],
            languages: ['zh-TW'],
            platforms: ['tiktok', 'youtube-shorts'],
            videoDuration: 30
          },
          budget: {
            dailyLimit: 10.0,
            monthlyLimit: 300.0,
            stopOnBudgetExceeded: true
          },
          quality: {
            minimumTrendScore: 0.7,
            contentQualityThreshold: 0.8
          },
          publishing: {
            autoPublish: false,
            scheduledPublishing: true,
            publishingHours: ['10:00', '14:00', '18:00']
          }
        }
      };
    } catch (error) {
      toastStore.error('Failed to load settings');
      console.error('Error loading settings:', error);
    } finally {
      isLoading = false;
    }
  }

  // Event handlers
  async function handleProfileSave(event) {
    const profileData = event.detail;
    try {
      isSaving = true;
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      settingsData.profile = { ...settingsData.profile, ...profileData };
      toastStore.success('Profile updated successfully!');
    } catch (error) {
      toastStore.error('Failed to update profile');
    } finally {
      isSaving = false;
    }
  }

  async function handleNotificationsSave(event) {
    const notificationData = event.detail;
    try {
      isSaving = true;
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      settingsData.notifications = notificationData;
      toastStore.success('Notification preferences saved!');
    } catch (error) {
      toastStore.error('Failed to save notification settings');
    } finally {
      isSaving = false;
    }
  }

  async function handleChangePassword(event) {
    const passwordData = event.detail;
    try {
      isSaving = true;
      
      // Validate passwords match
      if (passwordData.new_password !== passwordData.confirm_password) {
        toastStore.error('New passwords do not match');
        return;
      }
      
      if (passwordData.new_password.length < 8) {
        toastStore.error('Password must be at least 8 characters long');
        return;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      toastStore.success('Password changed successfully!');
    } catch (error) {
      toastStore.error('Failed to change password');
    } finally {
      isSaving = false;
    }
  }

  async function handleDeleteAccount() {
    try {
      isSaving = true;
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // In a real app, this would delete the account and log out
      toastStore.success('Account deletion request submitted');
    } catch (error) {
      toastStore.error('Failed to delete account');
    } finally {
      isSaving = false;
    }
  }

  function handleEnable2FA() {
    toastStore.info('2FA setup feature coming soon!');
  }

  function handleDisable2FA() {
    toastStore.info('2FA management feature coming soon!');
  }

  async function handleEntrepreneurModeSave(event) {
    const entrepreneurData = event.detail;
    try {
      isSaving = true;
      
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      settingsData.entrepreneurMode = { ...settingsData.entrepreneurMode, ...entrepreneurData };
      toastStore.success('創業者模式設定已更新！');
    } catch (error) {
      toastStore.error('Failed to update entrepreneur mode settings');
    } finally {
      isSaving = false;
    }
  }
</script>

<svelte:head>
  <title>Settings - AutoVideo</title>
</svelte:head>

<div class="p-6 max-w-7xl mx-auto">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
    <p class="mt-2 text-gray-600 dark:text-gray-400">
      Manage your account settings and preferences
    </p>
  </div>

  {#if isLoading}
    <LoadingSpinner size="lg" text="Loading settings..." />
  {:else}
    <div class="flex flex-col lg:flex-row lg:space-x-8">
      <!-- Sidebar Navigation -->
      <div class="lg:w-64 mb-8 lg:mb-0">
        <nav class="space-y-1">
          {#each tabs as tab}
            <button
              class="group flex items-center w-full px-3 py-2 text-sm font-medium rounded-md transition-colors {activeTab === tab.id
                ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900 dark:text-gray-400 dark:hover:bg-gray-800 dark:hover:text-gray-300'}"
              on:click={() => activeTab = tab.id}
            >
              <svelte:component 
                this={tab.icon} 
                class="mr-3 h-5 w-5 {activeTab === tab.id ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'}" 
              />
              <div class="text-left">
                <div class="font-medium">{tab.name}</div>
                <div class="text-xs text-gray-500 dark:text-gray-400 hidden lg:block">
                  {tab.description}
                </div>
              </div>
            </button>
          {/each}
        </nav>
      </div>

      <!-- Main Content -->
      <div class="flex-1 min-w-0">
        {#if activeTab === 'profile'}
          <ProfileSettings
            profile={settingsData.profile}
            isLoading={isSaving}
            on:save={handleProfileSave}
          />

        {:else if activeTab === 'entrepreneurMode'}
          <EntrepreneurModeSettings
            entrepreneurSettings={settingsData.entrepreneurMode}
            isLoading={isSaving}
            on:save={handleEntrepreneurModeSave}
          />

        {:else if activeTab === 'notifications'}
          <NotificationSettings
            notifications={settingsData.notifications}
            isLoading={isSaving}
            on:save={handleNotificationsSave}
          />

        {:else if activeTab === 'security'}
          <SecuritySettings
            isLoading={isSaving}
            on:changePassword={handleChangePassword}
            on:deleteAccount={handleDeleteAccount}
            on:enable2FA={handleEnable2FA}
            on:disable2FA={handleDisable2FA}
          />

        {:else if activeTab === 'privacy'}
          <!-- Privacy Settings Placeholder -->
          <div class="space-y-6">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Privacy Settings
              </h3>
              <p class="text-gray-500 dark:text-gray-400">
                Privacy settings interface will be implemented here.
              </p>
            </div>
          </div>

        {:else if activeTab === 'appearance'}
          <!-- Appearance Settings Placeholder -->
          <div class="space-y-6">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Appearance Settings
              </h3>
              <p class="text-gray-500 dark:text-gray-400">
                Theme and appearance customization will be implemented here.
              </p>
            </div>
          </div>

        {:else if activeTab === 'billing'}
          <!-- Billing Settings Placeholder -->
          <div class="space-y-6">
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Billing & Subscription
              </h3>
              <p class="text-gray-500 dark:text-gray-400">
                Billing and subscription management will be implemented here.
              </p>
              
              <div class="mt-6 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <div class="flex items-center">
                  <div class="flex-shrink-0">
                    <div class="w-8 h-8 bg-green-100 dark:bg-green-900/40 rounded-full flex items-center justify-center">
                      <SettingsIcon class="w-4 h-4 text-green-600 dark:text-green-400" />
                    </div>
                  </div>
                  <div class="ml-3">
                    <h4 class="text-sm font-medium text-green-800 dark:text-green-200">
                      Current Plan: {settingsData.billing.plan}
                    </h4>
                    <p class="text-sm text-green-700 dark:text-green-300">
                      Next billing: {new Date(settingsData.billing.nextBilling).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>