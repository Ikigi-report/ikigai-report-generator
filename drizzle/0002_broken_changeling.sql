ALTER TABLE `reports` ADD `secondaryName` varchar(160);--> statement-breakpoint
ALTER TABLE `reports` ADD `reportType` enum('personal','compatibility') DEFAULT 'personal' NOT NULL;--> statement-breakpoint
ALTER TABLE `reports` ADD `language` enum('en','ar') DEFAULT 'en' NOT NULL;