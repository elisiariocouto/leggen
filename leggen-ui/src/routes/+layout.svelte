<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Navbar from '$lib/components/Navbar.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="flex h-screen bg-gray-50">
	<Sidebar />
	<div class="flex-1 flex flex-col overflow-hidden">
		<Navbar />
		<main class="flex-1 overflow-x-hidden overflow-y-auto bg-white p-6">
			{@render children?.()}
		</main>
	</div>
</div>
