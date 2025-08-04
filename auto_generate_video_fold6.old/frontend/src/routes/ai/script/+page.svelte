<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast';
  import { goto } from '$app/navigation';

  // Import script components
  import ScriptGenerator from '$lib/components/ai/script/ScriptGenerator.svelte';
  import ScriptOutput from '$lib/components/ai/script/ScriptOutput.svelte';
  import TrendingSuggestions from '$lib/components/ai/script/TrendingSuggestions.svelte';
  import ScriptHistory from '$lib/components/ai/script/ScriptHistory.svelte';

  let isGenerating = false;
  let generatedScript = '';
  let scriptHistory = [];
  let showAdvanced = false;
  
  // Form data
  let formData = {
    topic: '',
    style: 'educational',
    tone: 'professional',
    duration: 60,
    platform: 'youtube',
    audience: 'general',
    keywords: '',
    hook_type: 'question',
    include_cta: true,
    language: 'en'
  };

  const trendingTopics = [
    { topic: 'AI productivity tools for 2024', difficulty: 'easy', potential: 'high' },
    { topic: 'Remote work best practices', difficulty: 'medium', potential: 'high' },
    { topic: 'Sustainable living tips', difficulty: 'easy', potential: 'medium' },
    { topic: 'Cryptocurrency investing guide', difficulty: 'hard', potential: 'high' },
    { topic: 'Social media marketing strategies', difficulty: 'medium', potential: 'high' }
  ];

  onMount(() => {
    loadScriptHistory();
  });

  async function loadScriptHistory() {
    try {
      // Simulate loading script history
      scriptHistory = [
        {
          id: 1,
          topic: 'AI Tools for Content Creators',
          script: 'Are you tired of spending hours creating content? What if I told you...',
          createdAt: new Date().toISOString(),
          performance: { score: 92, engagement: 8.5 }
        },
        {
          id: 2,
          topic: 'Remote Work Productivity Hacks',
          script: 'Working from home can be challenging, but these 5 simple tricks...',
          createdAt: new Date(Date.now() - 86400000).toISOString(),
          performance: { score: 87, engagement: 7.2 }
        }
      ];
    } catch (error) {
      console.error('Error loading script history:', error);
    }
  }

  async function generateScript() {
    if (!formData.topic.trim()) {
      toastStore.error('Please enter a topic for your script');
      return;
    }

    isGenerating = true;
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const mockScript = generateMockScript();
      generatedScript = mockScript;
      
      // Add to history
      scriptHistory.unshift({
        id: Date.now(),
        topic: formData.topic,
        script: mockScript.substring(0, 100) + '...',
        createdAt: new Date().toISOString(),
        performance: { score: Math.floor(Math.random() * 20) + 80, engagement: Math.random() * 3 + 7 }
      });
      
      toastStore.success('Script generated successfully!');
    } catch (error) {
      console.error('Error generating script:', error);
      toastStore.error('Failed to generate script. Please try again.');
    } finally {
      isGenerating = false;
    }
  }

  function generateMockScript() {
    const hooks = {
      question: `Did you know that ${formData.topic.toLowerCase()} could completely change your life?`,
      statistic: `97% of people don't know this secret about ${formData.topic.toLowerCase()}.`,
      story: `Last month, I discovered something incredible about ${formData.topic.toLowerCase()} that I have to share with you.`,
      controversial: `Everything you think you know about ${formData.topic.toLowerCase()} is wrong.`,
      how_to: `Here's exactly how to master ${formData.topic.toLowerCase()} in just ${formData.duration} seconds.`
    };

    const hook = hooks[formData.hook_type] || hooks.question;
    
    return `${hook}

In this video, I'm going to show you the most effective strategies for ${formData.topic.toLowerCase()} that actually work in ${new Date().getFullYear()}.

First, let me tell you why this matters. Most people struggle with ${formData.topic.toLowerCase()} because they're using outdated methods that simply don't work anymore.

Here are the key points you need to know:

1. The foundation: Understanding the basics is crucial
2. The advanced techniques: These will set you apart
3. Common mistakes: Avoid these pitfalls
4. Implementation: How to actually apply this

${formData.include_cta ? `If you found this helpful, make sure to subscribe and hit the notification bell for more content like this!` : ''}

Remember, success with ${formData.topic.toLowerCase()} comes down to consistency and the right approach. Start implementing these strategies today!`;
  }

  function handleGenerate() {
    generateScript();
  }

  function handleRegenerate() {
    generateScript();
  }

  function handleUseTrend(event) {
    const trend = event.detail;
    formData.topic = trend.topic;
    toastStore.info(`Using trending topic: ${trend.topic}`);
  }

  function handleCopyScript() {
    toastStore.success('Script copied to clipboard!');
  }

  function handleDownloadScript() {
    toastStore.success('Script downloaded successfully!');
  }

  function handleSaveScript() {
    toastStore.success('Script saved to history!');
  }

  function handleUseInProject() {
    goto('/create?script=' + encodeURIComponent(generatedScript));
  }

  function handleUseHistoryScript(event) {
    const script = event.detail;
    formData.topic = script.topic;
    generatedScript = script.script;
    toastStore.info('Script loaded from history');
  }

  function handleDeleteHistoryScript(event) {
    const scriptId = event.detail;
    scriptHistory = scriptHistory.filter(s => s.id !== scriptId);
    toastStore.success('Script deleted from history');
  }
</script>

<svelte:head>
  <title>AI Script Generator - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
      AI Script Generator
    </h1>
    <p class="text-gray-600 dark:text-gray-400">
      Generate engaging video scripts optimized for different platforms using AI
    </p>
  </div>

  <div class="grid lg:grid-cols-3 gap-8">
    <!-- Main Content -->
    <div class="lg:col-span-2 space-y-6">
      <!-- Script Generator -->
      <ScriptGenerator
        bind:formData
        bind:isGenerating
        bind:showAdvanced
        on:generate={handleGenerate}
        on:regenerate={handleRegenerate}
      />

      <!-- Generated Script Output -->
      <ScriptOutput
        script={generatedScript}
        topic={formData.topic}
        on:copy={handleCopyScript}
        on:download={handleDownloadScript}
        on:save={handleSaveScript}
        on:useInProject={handleUseInProject}
      />
    </div>

    <!-- Sidebar -->
    <div class="space-y-6">
      <!-- Trending Topics -->
      <TrendingSuggestions
        trends={trendingTopics}
        on:useTrend={handleUseTrend}
      />

      <!-- Script History -->
      <ScriptHistory
        history={scriptHistory}
        on:useScript={handleUseHistoryScript}
        on:deleteScript={handleDeleteHistoryScript}
      />
    </div>
  </div>
</div>