
class Server {
    public apiUrl: string | null;
    constructor() {
        const next_env = process.env.NODE_ENV || 'development';
        const urls = { localApi: 'http://127.0.0.1:5000', productionApi: null };
        this.apiUrl = next_env === 'production' ? urls.productionApi : urls.localApi;
    }
}
export default Server;