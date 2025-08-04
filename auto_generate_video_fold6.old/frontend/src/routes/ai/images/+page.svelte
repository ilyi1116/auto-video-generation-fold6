<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast';

  // Import image components
  import ImageGenerator from '$lib/components/ai/images/ImageGenerator.svelte';
  import ImageGallery from '$lib/components/ai/images/ImageGallery.svelte';

  let isGenerating = false;
  let generatedImages = [];
  let selectedImages = new Set();
  let viewMode = 'grid';
  let showAdvanced = false;
  
  // Form data
  let formData = {
    prompt: '',
    style: 'realistic',
    aspect_ratio: '16:9',
    quality: 'standard',
    count: 4,
    negative_prompt: '',
    seed: '',
    guidance_scale: 7.5,
    steps: 20
  };

  async function generateImages() {
    if (!formData.prompt.trim()) {
      toastStore.error('Please enter a description for your images');
      return;
    }

    isGenerating = true;
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 4000));
      
      const newImages = Array.from({ length: formData.count }, (_, i) => ({
        id: Date.now() + i,
        prompt: formData.prompt,
        style: formData.style,
        aspect_ratio: formData.aspect_ratio,
        quality: formData.quality,
        createdAt: new Date().toISOString(),
        liked: false
      }));
      
      generatedImages = [...newImages, ...generatedImages];
      toastStore.success(`Generated ${formData.count} images successfully!`);
    } catch (error) {
      console.error('Error generating images:', error);
      toastStore.error('Failed to generate images. Please try again.');
    } finally {
      isGenerating = false;
    }
  }

  function handleGenerate() {
    generateImages();
  }

  function handleDownload(event) {
    const image = event.detail;
    toastStore.success('Image downloaded successfully!');
  }

  function handleLike(event) {
    const image = event.detail;
    const index = generatedImages.findIndex(img => img.id === image.id);
    if (index !== -1) {
      generatedImages[index].liked = !generatedImages[index].liked;
      generatedImages = [...generatedImages];
    }
    toastStore.success(generatedImages[index].liked ? 'Added to favorites' : 'Removed from favorites');
  }

  function handleShare(event) {
    const image = event.detail;
    toastStore.success('Share options opened');
  }

  function handleDelete(event) {
    const image = event.detail;
    generatedImages = generatedImages.filter(img => img.id !== image.id);
    selectedImages.delete(image.id);
    selectedImages = new Set(selectedImages);
    toastStore.success('Image deleted');
  }

  function handleSelectionChange(event) {
    selectedImages = event.detail;
  }
</script>

<svelte:head>
  <title>AI Image Generator - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
      AI Image Generator
    </h1>
    <p class="text-gray-600 dark:text-gray-400">
      Create stunning visuals for your videos using advanced AI technology
    </p>
  </div>

  <div class="grid lg:grid-cols-3 gap-8">
    <!-- Generator -->
    <div class="lg:col-span-1">
      <ImageGenerator
        bind:formData
        bind:isGenerating
        bind:showAdvanced
        on:generate={handleGenerate}
      />
    </div>

    <!-- Gallery -->
    <div class="lg:col-span-2">
      <ImageGallery
        images={generatedImages}
        bind:viewMode
        bind:selectedImages
        on:download={handleDownload}
        on:like={handleLike}
        on:share={handleShare}
        on:delete={handleDelete}
        on:selectionChange={handleSelectionChange}
      />
    </div>
  </div>

  <!-- Bulk Actions -->
  {#if selectedImages.size > 0}
    <div class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white dark:bg-gray-800 shadow-lg border dark:border-gray-700 rounded-lg px-6 py-3 z-50">
      <div class="flex items-center space-x-4">
        <span class="text-sm font-medium text-gray-900 dark:text-white">
          {selectedImages.size} image{selectedImages.size > 1 ? 's' : ''} selected
        </span>
        
        <div class="flex items-center space-x-2">
          <button
            type="button"
            class="btn-secondary text-sm"
            on:click={() => toastStore.success('Bulk download started')}
          >
            Download All
          </button>
          
          <button
            type="button"
            class="btn-secondary text-sm"
            on:click={() => toastStore.success('Added to project')}
          >
            Add to Project
          </button>
          
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            on:click={() => selectedImages = new Set()}
          >
            ✕
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>