CREATE TABLE `reports` (
	`id` int AUTO_INCREMENT NOT NULL,
	`userId` int NOT NULL,
	`recipientName` varchar(160) NOT NULL,
	`birthDate` varchar(10) NOT NULL,
	`birthPlace` text NOT NULL,
	`status` enum('ready','failed') NOT NULL DEFAULT 'ready',
	`markdownKey` varchar(512) NOT NULL,
	`calculationsKey` varchar(512) NOT NULL,
	`pdfKey` varchar(512),
	`errorMessage` text,
	`createdAt` timestamp NOT NULL DEFAULT (now()),
	`updatedAt` timestamp NOT NULL DEFAULT (now()) ON UPDATE CURRENT_TIMESTAMP,
	CONSTRAINT `reports_id` PRIMARY KEY(`id`)
);
--> statement-breakpoint
CREATE INDEX `reports_user_created_idx` ON `reports` (`userId`,`createdAt`);