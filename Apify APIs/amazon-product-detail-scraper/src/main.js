import { Actor,log } from 'apify';
import axios from 'axios';
import { URL } from 'url';
import 'dotenv/config';
import Bottleneck from 'bottleneck';

const API_KEY = process.env.AMAZON_API_KEY;

function searchUrls(text) {
    const urlPattern = /(https?:\/\/(?:www\.)?[-\w]+(?:\.\w[-\w]*)+(:\d+)?(?:\/[^.!,?;"'<>()[\]{}\s\x7F-\xFF]*(?:[.!,?]+[^.!,?;"'<>()[\]{}\s\x7F-\xFF]+)?)?)/g;
    const urls = text.match(urlPattern);
    return urls || []; // Return an empty array if no URLs are found
}

async function loadDataFromUrl(url) {
    try {
        const response = await axios.get(url);
        return searchUrls(response.data);
    } catch (error) {
        console.error('Error fetching data:', error.message);
        throw error;
    }
}

async function processRequest(request) {
    let response = null;
    const data = {
        url: request.url,
        key: API_KEY,
        method: 'get',
    };

    try {
        response = await axios.post('https://api.syphoon.com', data, { timeout: 60000 });

        if (response.status >= 200 && response.status < 300) {
            return { request, response };
        }

    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (request.retryCount > 0) {
                request.retryCount--;
            }
            console.error('Request failed:', error.message);
        }
    }
    return { request, response };
}

const MAX_CONCURRENT_REQUESTS = 5;
const REQUESTS_PER_SECOND = 2;

async function main() {
    await Actor.init();

    const actorInput = await Actor.getInput() || {};
    const inputUrls = actorInput.urls || [];

    const remainingUrlsDataset = await Actor.openDataset('remaining-urls');
    let urls = [];
    let defaultQueue = [];

    try {
        for (const inputUrl of inputUrls) {
            if (inputUrl.requestsFromUrl && inputUrl.requestsFromUrl !== '') {
                const loadedUrls = await loadDataFromUrl(inputUrl.requestsFromUrl);
                urls = urls.concat(loadedUrls);
            } else if (inputUrl.url) {
                urls.push(inputUrl.url);
            }
        }
    } catch (error) {
        log.info('Cannot load data from File.');
        Actor.fail('Cannot load data from File.');
    }

    log.info(`Enqueuing ${urls.length} urls...`);

    for (let url of urls) {
        if (typeof url === 'object' && url.url) url = url.url;
        if (typeof url === 'string') {
            const parsedUrl = new URL(url);
            if (!url.startsWith('https') || !parsedUrl.hostname.includes('amazon')) continue;
            defaultQueue.push({ url, retryCount: 3 });
        }
    }

    const limiter = new Bottleneck({
        maxConcurrent: MAX_CONCURRENT_REQUESTS,
        minTime: 1000 / REQUESTS_PER_SECOND,
    });

    async function processWithLimiter(request) {
        return limiter.schedule(() => processRequest(request));
    }

    while (defaultQueue.length > 0) {
        const batch = defaultQueue.splice(0, MAX_CONCURRENT_REQUESTS);
        const requestTasks = batch.map((request) => processWithLimiter(request));
        const start = Date.now();
        const results = await Promise.allSettled(requestTasks);

        log.info(`Processed ${results.length} requests in ${(Date.now() - start) / 1000} seconds`);

        for (const result of results) {
            const { status, value } = result;

            if (status === 'fulfilled') {
                const { request, response } = value;

                if (response && response.status === 200) {
                    await Actor.pushData(response.data);
                } else if (response) {
                    await Actor.pushData(response.data);
                }
                else if (request.retryCount > 0) {
                    defaultQueue.push(request);
                    console.log(`Retrying ${request.url}...`);
                }
            } else {
                const request = result.value.request;
                if (request.retryCount > 0) {
                    defaultQueue.push(request);
                    console.log(`Retrying ${request.url}...`);
                } else {
                    await remainingUrlsDataset.pushData({ url: request.url });
                }
            }
        }
        log.info(`Batch of requests processed in ${(Date.now() - start) / 1000} seconds`);
    }

    await Actor.exit();
}

main().catch((error) => {
    console.error('Error running the actor:', error);
});
