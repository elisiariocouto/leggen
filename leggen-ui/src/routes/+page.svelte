<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import {
		Table,
		TableBody,
		TableCell,
		TableHead,
		TableHeader,
		TableRow
	} from '$lib/components/ui/table';

	// Mock transaction data
	const transactions = [
		{
			id: '1',
			date: '2024-01-15',
			description: 'Grocery Store Purchase',
			amount: -45.32,
			category: 'Food & Dining',
			account: 'Checking Account'
		},
		{
			id: '2',
			date: '2024-01-14',
			description: 'Salary Deposit',
			amount: 2500.00,
			category: 'Income',
			account: 'Checking Account'
		},
		{
			id: '3',
			date: '2024-01-13',
			description: 'Coffee Shop',
			amount: -4.75,
			category: 'Food & Dining',
			account: 'Credit Card'
		},
		{
			id: '4',
			date: '2024-01-12',
			description: 'Electric Bill',
			amount: -89.50,
			category: 'Utilities',
			account: 'Checking Account'
		},
		{
			id: '5',
			date: '2024-01-11',
			description: 'Online Shopping',
			amount: -156.23,
			category: 'Shopping',
			account: 'Credit Card'
		}
	];

	function formatAmount(amount: number): string {
		const formatted = Math.abs(amount).toFixed(2);
		return amount >= 0 ? `+$${formatted}` : `-$${formatted}`;
	}

	function getAmountClass(amount: number): string {
		return amount >= 0 ? 'text-green-600' : 'text-red-600';
	}
</script>

<div class="space-y-6">
	<div class="flex justify-between items-center">
		<div>
			<h1 class="text-3xl font-bold text-gray-900">Dashboard</h1>
			<p class="text-gray-600 mt-1">Overview of your financial transactions</p>
		</div>
		<Button>Sync Transactions</Button>
	</div>

	<div class="bg-white rounded-lg shadow">
		<div class="px-6 py-4 border-b border-gray-200">
			<h2 class="text-lg font-semibold text-gray-900">Recent Transactions</h2>
		</div>

		<div class="overflow-x-auto">
			<Table>
				<TableHeader>
					<TableRow>
						<TableHead>Date</TableHead>
						<TableHead>Description</TableHead>
						<TableHead>Category</TableHead>
						<TableHead>Account</TableHead>
						<TableHead class="text-right">Amount</TableHead>
					</TableRow>
				</TableHeader>
				<TableBody>
					{#each transactions as transaction}
						<TableRow>
							<TableCell class="font-medium">{transaction.date}</TableCell>
							<TableCell>{transaction.description}</TableCell>
							<TableCell>{transaction.category}</TableCell>
							<TableCell>{transaction.account}</TableCell>
							<TableCell class="text-right {getAmountClass(transaction.amount)} font-medium">
								{formatAmount(transaction.amount)}
							</TableCell>
						</TableRow>
					{/each}
				</TableBody>
			</Table>
		</div>
	</div>
</div>
