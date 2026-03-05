// index.js
const app = getApp()

Page({
  data: {
    // UI State
    activeTab: 'home',
    activeCategory: '全部',
    activeRatingTag: '全部',
    navBarHeight: 0,
    statusBarHeight: 0,
    totalHeaderHeight: 0,
    menuButtonWidth: 0,
    
    // Modals
    showLogin: false,
    showAuth: false,
    showPost: false,
    showDetail: false,
    showComments: false,
    showGoods: false,
    showOrder: false,
    showRunner: false,
    showApplicants: false,
    showMap: false,
    showRecruit: false,
    showUpload: false,
    showRatingRequest: false,
    showMyPosts: false,
    showGroup: false,
    showSettings: false,
    showSchool: false,
    showFilter: false,
    showRoom: false,

    // Data
    userInfo: { nickName: '未登录用户', avatarUrl: '' },
    authed: false,
    school: '',
    theme: 'dark',
    dnd: false,
    marketingOff: false,
    points: 0,
    unreadCount: 0,
    postsCount: 0,
    goodsCount: 0,
    textSize: 'medium',
    postCategories: ['学习互助', '娱乐休闲', '兴趣爱好', '竞赛科研'],
    postCategory: '学习互助',
    
    // Mock Data
    posts: [
      { id: 1, avatarColor: 'orange', name: '计科23级 · 林同学', time: '1小时前 · 图书馆', content: '今晚求一起复习数据结构，限本校，地点在二教402。', detail: '标题：寻找学习搭子一起备战期末\n内容：本人大二计算机专业，想找一位同学一起复习高数和数据结构，每天晚上在图书馆学习，有意向的同学可以联系我~', img: 'https://picsum.photos/seed/campus1/300/200', likes: 36, comments: 2, category: '学习互助', commentList: ['同学A：一起复习我也报名', '同学B：周五晚上可以吗'] },
      { id: 2, avatarColor: 'pink', name: '传媒21级 · 周同学', time: '5小时前 · 影视厅', content: '周末一起观影讨论《人工智能与社会》，限5人。', detail: '标题：观影讨论招募\n内容：周末晚间在影视厅组织观影并讨论，欢迎感兴趣同学参加。', likes: 22, comments: 1, category: '娱乐休闲', commentList: ['我想报名参加'] },
      { id: 3, avatarColor: 'blue', name: '物理22级 · 郑同学', time: '3小时前 · 宿舍', content: '有无羽毛球搭子，周五晚体育馆三号场，限三人。', detail: '标题：羽毛球搭子招募\n内容：周五晚体育馆三号场，技术不限，主打锻炼。', likes: 18, comments: 0, category: '兴趣爱好', commentList: [] },
      { id: 4, avatarColor: 'cyan', name: '电气24级 · 唐同学', time: '2小时前 · 创客空间', content: '招募机器人竞赛队员，机械/嵌入式/算法均可。', detail: '标题：机器人竞赛招募\n内容：面向校内招募机器人竞赛队员，可参与机械、嵌入式、算法。', likes: 41, comments: 1, category: '竞赛科研', commentList: ['已投递简历'] }
    ],
    marketItems: [
      { id: 1, title: '二手考研资料全套', sub: '理工校区 · 可自提', price: '89', color: '', owner: '理工校区 · 李同学', desc: '九成新，含重点笔记，可当面验货。', image: 'https://picsum.photos/seed/market1/120/120' },
      { id: 2, title: '二手耳机 Sony WH-1000XM4', sub: '理工校区 · 可试戴', price: '950', color: 'linear-gradient(135deg,#7ef0c6,#7aa3ff)', owner: '理工校区 · 陈同学', desc: '正常使用一年，降噪正常，配件齐全。', image: 'https://picsum.photos/seed/market2/120/120' },
      { id: 3, title: '考研数学教材套装', sub: '西区 · 可自提', price: '120', color: 'linear-gradient(135deg,#ffcf5c,#ffd39b)', owner: '西区 · 周同学', desc: '包含真题与讲义，页内有少量标注。', image: 'https://picsum.photos/seed/market3/120/120' },
      { id: 4, title: '自行车九成新', sub: '东区 · 支持试骑', price: '220', color: 'linear-gradient(135deg,#ff9b9b,#ffd39b)', owner: '东区 · 郑同学', desc: '可短途骑行，刹车和变速正常。', image: 'https://picsum.photos/seed/market4/120/120' }
    ],
    ratingItems: [
      { id: 1, title: '张老师 · 数据结构', score: '4.6', sub: '课程难度适中 · 讲解清晰', tag: '老师', color: '', ratingSum: 46, ratingCount: 10, reviewCount: 2, reviews: [{ user: '李同学', stars: 5, reason: '讲课很细致，作业反馈及时。', createdAt: 1710000000000 }, { user: '王同学', stars: 4, reason: '内容扎实，课堂节奏偏快。', createdAt: 1710001000000 }] },
      { id: 2, title: '算法期末复习提纲', score: '4.7', sub: '覆盖常见题型 · 讲义条理清晰', tag: '资料', color: 'linear-gradient(135deg,#7aa3ff,#ffd39b)', ratingSum: 47, ratingCount: 10, reviewCount: 1, reviews: [{ user: '陈同学', stars: 5, reason: '重点归纳清晰，临考很有帮助。', createdAt: 1710002000000 }] },
      { id: 3, title: '南区二食堂', score: '4.4', sub: '口味丰富 · 卫生良好 · 性价比高', tag: '食堂', color: 'linear-gradient(135deg,#ff9b9b,#7ef0c6)', ratingSum: 44, ratingCount: 10, reviewCount: 0, reviews: [] },
      { id: 4, title: '理工打印店', score: '4.3', sub: '价格透明 · 出图较快', tag: '商铺', color: 'linear-gradient(135deg,#7ef0c6,#7aa3ff)', ratingSum: 43, ratingCount: 10, reviewCount: 0, reviews: [] },
      { id: 5, title: '高等数学A', score: '4.8', sub: '题库完善 · 讲义齐全', tag: '课程', color: 'linear-gradient(135deg,#ffcf5c,#7ef0c6)', ratingSum: 48, ratingCount: 10, reviewCount: 1, reviews: [{ user: '赵同学', stars: 5, reason: '题库覆盖全，复习效率很高。', createdAt: 1710003000000 }] }
    ],
    chatItems: [
      { id: 1, name: '林同学', msg: '今晚复习安排确认', tag: '未读 2', source: '圈子消息', roomType: '私聊', color: '' },
      { id: 2, name: '二手卖家 · 陈同学', msg: '耳机还在，可现场试听', tag: '已读', source: '集市消息', roomType: '私聊', color: 'linear-gradient(135deg,#7aa3ff,#7ef0c6)' },
      { id: 3, name: '组队群聊 · 机器人竞赛', msg: '本周任务分配与联调安排', tag: '未读 1', source: '评分消息', roomType: '群聊', color: 'linear-gradient(135deg,#7ef0c6,#7aa3ff)' }
    ],
    
    // Temporary State
    detailTitle: '',
    detailBody: '',
    detailPostId: null,
    detailType: '',
    detailContactName: '',
    detailRatingId: null,
    detailRatingReviews: [],
    detailImage: '',
    detailChatSeed: [],
    isDetailFavorited: false,
    ratingStars: 5,
    ratingText: '',
    ratingReqCategory: '',
    ratingReqReason: '',
    ratingReqStars: 5,
    ratingReqFiles: [],
    groupAvatar: '',
    commentsTitle: '',
    currentCommentPostId: null,
    roomTitle: '',
    roomPeerName: '',
    roomSelfName: '',
    favoritePostIds: [],
    comments: [],
    chatMessages: [
      { text: '你好，请问今晚能一起复习吗', isMe: false },
      { text: '可以，图书馆二楼自习区见', isMe: true }
    ],
    commentInput: '',
    msgInput: '',
    routeInput: '',
    routeHint: '已标注建筑开放时间、楼层指引、内部设施分布。',
    circleSearchKeyword: '',
    filteredPosts: [],
    filteredRatingItems: [],
    chatFilter: '全部',
    filteredChatItems: [],
    ratingLogs: [],
    marketImages: [],
    interests: ['竞技体育', '编程开发', '音乐艺术', '公益志愿'],
    selectedInterests: [],
    customInterestInput: '',
    orderIntents: [],
    myPublishTab: '圈子'
  },

  onLoad() {
    this.calcHeader()
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      this.setData({ userInfo, authed: true })
    }
    this.applyCategory(this.data.activeCategory)
    this.applyRatingCategory(this.data.activeRatingTag)
    this.applyChatFilter(this.data.chatFilter)
    this.syncUnreadCount()
    this.setData({
      postsCount: this.data.posts.length,
      goodsCount: this.data.marketItems.length
    })
  },

  calcHeader() {
    const sysInfo = wx.getSystemInfoSync()
    const menuButtonInfo = wx.getMenuButtonBoundingClientRect()
    const statusBarHeight = sysInfo.statusBarHeight
    const navBarHeight = (menuButtonInfo.top - statusBarHeight) * 2 + menuButtonInfo.height
    
    this.setData({
      statusBarHeight,
      navBarHeight,
      totalHeaderHeight: statusBarHeight + navBarHeight,
      menuButtonWidth: sysInfo.windowWidth - menuButtonInfo.left
    })
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab })
  },

  onCircleSearchInput(e) {
    const circleSearchKeyword = ((e.detail && e.detail.value) || '').trim()
    this.setData({ circleSearchKeyword })
    this.applyCategory(this.data.activeCategory)
  },

  selectCategory(e) {
    const cat = e.currentTarget.dataset.cat
    this.applyCategory(cat)
  },

  applyCategory(cat, sourcePosts) {
    const basePosts = sourcePosts || this.data.posts
    const keyword = (this.data.circleSearchKeyword || '').toLowerCase()
    const byCat = cat === '全部' ? basePosts : basePosts.filter(post => post.category === cat)
    const filteredPosts = keyword ? byCat.filter(post => `${post.content} ${post.detail || ''}`.toLowerCase().includes(keyword)) : byCat
    this.setData({
      activeCategory: cat,
      filteredPosts
    })
  },

  selectRatingCategory(e) {
    const tag = e.currentTarget.dataset.tag
    this.applyRatingCategory(tag)
  },

  applyRatingCategory(tag) {
    const filteredRatingItems = tag === '全部' ? this.data.ratingItems : this.data.ratingItems.filter(item => item.tag === tag)
    this.setData({
      activeRatingTag: tag,
      filteredRatingItems
    })
  },

  // --- Login & Auth ---
  openLogin() { this.setData({ showLogin: true }) },
  closeLogin() { this.setData({ showLogin: false }) },
  
  doLogin() {
    const userInfo = { nickName: '微信用户', avatarUrl: '' }
    wx.setStorageSync('userInfo', userInfo)
    this.setData({ 
      userInfo, 
      showLogin: false, 
      authed: true,
      school: '理工校区'
    })
    this.addPoints(1)
    wx.showToast({ title: '登录成功' })
  },

  openAuth() { this.setData({ showAuth: true, showLogin: false }) },
  closeAuth() { this.setData({ showAuth: false }) },
  
  submitAuth(e) {
    const { id, name } = e.detail.value
    if (!id || !name) return wx.showToast({ title: '请填写完整', icon: 'none' })
    
    this.setData({
      authed: true,
      'userInfo.nickName': name,
      showAuth: false
    })
    wx.showToast({ title: '认证成功' })
  },

  // --- Post ---
  openPost() {
    if (!this.data.authed) return this.openLogin()
    this.setData({ showPost: true, postCategory: '学习互助' })
  },
  closePost() { this.setData({ showPost: false }) },
  selectPostCategory(e) {
    this.setData({ postCategory: e.currentTarget.dataset.cat })
  },
  
  publishPost(e) {
    const { title, content } = e.detail.value
    if (!title || !content) return wx.showToast({ title: '请填写完整', icon: 'none' })
    
    const newPost = {
      id: Date.now(),
      avatarColor: 'orange',
      name: this.data.userInfo.nickName,
      time: '刚刚 · ' + (this.data.school || '本校'),
      content: content,
      detail: `标题：${title}\n内容：${content}`,
      likes: 0,
      comments: 0,
      category: this.data.postCategory,
      commentList: []
    }
    
    this.setData({
      posts: [newPost, ...this.data.posts],
      showPost: false,
      postsCount: this.data.postsCount + 1
    })
    this.applyCategory(this.data.activeCategory, [newPost, ...this.data.posts])
    this.addPoints(5)
    wx.showToast({ title: '发布成功' })
  },

  // --- Detail & Interaction ---
  openDetail(e) {
    const title = e.currentTarget.dataset.title || '详情'
    const type = e.currentTarget.dataset.type || 'post'
    const contact = e.currentTarget.dataset.contact || ''
    const ratingIdRaw = Number(e.currentTarget.dataset.ratingId)
    const detailRatingId = Number.isFinite(ratingIdRaw) ? ratingIdRaw : null
    const rawId = Number(e.currentTarget.dataset.id)
    const id = Number.isFinite(rawId) ? rawId : null
    const isDetailFavorited = type === 'post' && id !== null ? this.data.favoritePostIds.includes(id) : false
    const post = id !== null ? this.data.posts.find(item => item.id === id) : null
    const rating = detailRatingId !== null ? this.data.ratingItems.find(item => item.id === detailRatingId) : null
    const market = id !== null ? this.data.marketItems.find(item => item.id === id) : null
    const intent = id !== null ? this.data.orderIntents.find(item => item.id === id) : null
    let detailBody = '详情内容展示区域...'
    let detailImage = ''
    let detailContactName = contact || '发布同学'
    let detailChatSeed = []
    let detailRatingReviews = []
    if (type === 'post' && post) {
      detailBody = post.detail || post.content
      detailContactName = post.name || detailContactName
    } else if (type === 'market' && market) {
      detailBody = `商品：${market.title}\n发布人：${market.owner || '发布同学'}\n价格：¥${market.price}\n说明：${market.desc || '暂无详情介绍'}`
      detailImage = market.image || ''
      detailContactName = market.owner || detailContactName
      detailChatSeed = [
        { sender: '我', text: `您好，请问${market.title}还在吗？`, isMe: true },
        { sender: market.owner || '卖家', text: `在的，${market.desc || '状态正常'}。`, isMe: false },
        { sender: '我', text: '多少钱呀？支持自提吗？', isMe: true },
        { sender: market.owner || '卖家', text: `¥${market.price}，支持在图书馆门口自提。`, isMe: false }
      ]
    } else if (type === 'intent' && intent) {
      detailBody = `求购物品：${intent.item}\n预算：${intent.budget}\n需求：${intent.desc}`
      detailContactName = intent.owner || detailContactName
      detailChatSeed = [
        { sender: intent.owner || '发布者', text: `你好，我有${intent.item}，想了解你的预算范围。`, isMe: false },
        { sender: '我', text: `你好，我预算是${intent.budget}，方便看下成色吗？`, isMe: true }
      ]
    } else if (type === 'rating' && rating) {
      detailBody = `${rating.title}\n当前评分：${rating.score}\n${rating.sub}`
      detailRatingReviews = (rating.reviews || []).slice().sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0))
    }
    this.setData({ 
      showDetail: true,
      detailTitle: title,
      detailBody,
      detailPostId: id,
      detailType: type,
      detailContactName,
      detailRatingId,
      detailRatingReviews,
      detailImage,
      detailChatSeed,
      isDetailFavorited,
      ratingStars: 5,
      ratingText: ''
    })
  },
  closeDetail() { this.setData({ showDetail: false }) },

  likePost(e) {
    const id = Number(e.currentTarget.dataset.id)
    if (!id) return
    const posts = this.data.posts.map(post => {
      if (post.id !== id) return post
      const liked = !post.liked
      const likes = liked ? post.likes + 1 : Math.max(0, post.likes - 1)
      return { ...post, liked, likes }
    })
    const activeCategory = this.data.activeCategory
    this.setData({ posts, activeCategory })
    this.applyCategory(activeCategory, posts)
  },

  toggleFavorite() {
    if (this.data.detailType !== 'post') return
    const id = this.data.detailPostId
    if (!id) return wx.showToast({ title: '该内容暂不支持收藏', icon: 'none' })
    const favoritePostIds = this.data.favoritePostIds.slice()
    const idx = favoritePostIds.indexOf(id)
    let isDetailFavorited = false
    if (idx > -1) {
      favoritePostIds.splice(idx, 1)
      wx.showToast({ title: '已取消收藏', icon: 'none' })
    } else {
      favoritePostIds.push(id)
      isDetailFavorited = true
      wx.showToast({ title: '收藏成功', icon: 'none' })
    }
    this.setData({ favoritePostIds, isDetailFavorited })
  },

  openContactFromDetail() {
    const name = this.data.detailContactName || '发布同学'
    const selfName = this.data.userInfo.nickName || '我'
    const chatMessages = (this.data.detailChatSeed.length ? this.data.detailChatSeed.slice() : this.data.chatMessages).map(msg => ({
      sender: msg.isMe ? selfName : (msg.sender || name),
      text: msg.text,
      isMe: msg.isMe
    }))
    this.setData({
      showDetail: false,
      showRoom: true,
      roomTitle: `发布人：${name}`,
      roomPeerName: name,
      roomSelfName: selfName,
      chatMessages
    })
  },

  openRatingRequest(e) {
    const ratingIdRaw = Number(e && e.currentTarget && e.currentTarget.dataset ? e.currentTarget.dataset.ratingId : 0)
    const ratingItem = this.data.ratingItems.find(item => item.id === ratingIdRaw) || this.data.ratingItems[0] || null
    this.setData({
      showRatingRequest: true,
      detailRatingId: ratingItem ? ratingItem.id : this.data.detailRatingId,
      ratingReqCategory: ratingItem ? ratingItem.tag : '',
      ratingReqReason: '',
      ratingReqStars: 5,
      ratingReqFiles: []
    })
  },
  closeRatingRequest() { this.setData({ showRatingRequest: false }) },
  setRatingReqCategory(e) {
    this.setData({ ratingReqCategory: e.currentTarget.dataset.cat })
  },
  setRatingReqStars(e) {
    const value = Number(e.currentTarget.dataset.value)
    if (!value) return
    this.setData({ ratingReqStars: value })
  },
  onRatingReqReasonInput(e) {
    this.setData({ ratingReqReason: (e.detail && e.detail.value) || '' })
  },
  chooseRatingFiles() {
    wx.chooseMessageFile({
      count: 3,
      type: 'file',
      success: (res) => {
        const files = (res.tempFiles || []).map(item => item.name || '附件')
        this.setData({ ratingReqFiles: files })
      }
    })
  },
  submitRatingRequest() {
    const { ratingReqCategory, ratingReqReason, ratingReqStars, ratingReqFiles } = this.data
    if (!ratingReqCategory || !ratingReqReason.trim() || !ratingReqStars) return wx.showToast({ title: '请完整填写评分信息', icon: 'none' })
    const ratingId = this.data.detailRatingId
    if (!ratingId) return wx.showToast({ title: '请选择评分对象', icon: 'none' })
    const user = this.data.userInfo.nickName || '我'
    const createdAt = Date.now()
    const ratingItems = this.data.ratingItems.map(item => {
      if (item.id !== ratingId) return item
      const ratingSum = (item.ratingSum || 0) + ratingReqStars
      const ratingCount = (item.ratingCount || 0) + 1
      const score = (ratingSum / ratingCount).toFixed(1)
      const reviews = [{ user, stars: ratingReqStars, reason: ratingReqReason, createdAt }, ...(item.reviews || [])]
      return { ...item, ratingSum, ratingCount, score, reviewCount: reviews.length, reviews }
    })
    this.setData({ ratingItems, showRatingRequest: false })
    if (this.data.showDetail && this.data.detailType === 'rating') {
      const current = ratingItems.find(item => item.id === ratingId)
      this.setData({ detailRatingReviews: (current && current.reviews ? current.reviews.slice() : []).sort((a, b) => (b.createdAt || 0) - (a.createdAt || 0)) })
    }
    this.applyRatingCategory(this.data.activeRatingTag)
    wx.showToast({ title: '评分已提交' })
  },

  setRatingStars(e) {
    const value = Number(e.currentTarget.dataset.value)
    if (!value) return
    this.setData({ ratingStars: value })
  },

  onRatingTextInput(e) {
    this.setData({ ratingText: (e.detail && e.detail.value) || '' })
  },

  submitRating() {
    if (this.data.detailType !== 'rating') return
    const ratingId = this.data.detailRatingId
    const stars = this.data.ratingStars
    const text = (this.data.ratingText || '').trim()
    if (!text) return wx.showToast({ title: '请填写评价内容', icon: 'none' })
    const ratingItems = this.data.ratingItems.map(item => {
      if (item.id !== ratingId) return item
      const ratingSum = (item.ratingSum || 0) + stars
      const ratingCount = (item.ratingCount || 0) + 1
      const score = (ratingSum / ratingCount).toFixed(1)
      return { ...item, ratingSum, ratingCount, score }
    })
    this.setData({
      ratingItems,
      showDetail: false
    })
    const ratingLogs = [{ id: Date.now(), title: this.data.detailTitle, stars, text }, ...this.data.ratingLogs]
    this.setData({ ratingLogs })
    this.applyRatingCategory(this.data.activeRatingTag)
    wx.showToast({ title: '评分已提交' })
  },

  openComments(e) {
    const title = e.currentTarget.dataset.title || '评论'
    const id = Number(e.currentTarget.dataset.id)
    const post = this.data.posts.find(item => item.id === id)
    this.setData({ 
      showComments: true, 
      commentsTitle: title,
      currentCommentPostId: id,
      comments: post && post.commentList ? post.commentList.slice() : []
    })
  },
  closeComments() { this.setData({ showComments: false }) },
  
  sendComment(e) {
    const val = ((e && e.detail && typeof e.detail.value === 'string' ? e.detail.value : this.data.commentInput) || '').trim()
    if (!val) return
    const comments = this.data.comments.slice()
    comments.push(`我：${val}`)
    const currentCommentPostId = this.data.currentCommentPostId
    const posts = this.data.posts.map(post => {
      if (post.id !== currentCommentPostId) return post
      const commentList = comments.slice()
      return { ...post, comments: commentList.length, commentList }
    })
    wx.showToast({ title: '评论已发布' })
    this.setData({ comments, commentInput: '', posts })
    this.applyCategory(this.data.activeCategory, posts)
  },

  // --- Market ---
  openGoods() {
    if (!this.data.authed) return this.openLogin()
    this.setData({ showGoods: true })
  },
  closeGoods() { this.setData({ showGoods: false }) },
  
  submitGoods(e) {
    const { title, price, desc } = e.detail.value
    if (!title || !price || !desc) return wx.showToast({ title: '请完善商品信息', icon: 'none' })
    const imageCount = this.data.marketImages.length
    const nextItems = [{
      id: Date.now(),
      title,
      price,
      sub: `${this.data.school || '本校'} · ${imageCount}张图`,
      color: 'linear-gradient(135deg,#7ef0c6,#7aa3ff)',
      owner: `${this.data.school || '本校'} · ${this.data.userInfo.nickName || '发布同学'}`,
      desc,
      image: this.data.marketImages[0] || ''
    }, ...this.data.marketItems]
    this.setData({
      marketItems: nextItems,
      showGoods: false,
      goodsCount: this.data.goodsCount + 1,
      marketImages: []
    })
    this.addPoints(5)
    wx.showToast({ title: '商品已发布' })
  },
  
  chooseGoodsImages() {
    const remain = Math.max(0, 6 - this.data.marketImages.length)
    if (!remain) return wx.showToast({ title: '最多上传6张', icon: 'none' })
    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      success: (res) => {
        const files = (res.tempFiles || []).map(item => item.tempFilePath)
        this.setData({ marketImages: [...this.data.marketImages, ...files] })
      }
    })
  },

  removeGoodsImage(e) {
    const index = Number(e.currentTarget.dataset.index)
    if (!Number.isFinite(index)) return
    const marketImages = this.data.marketImages.slice()
    marketImages.splice(index, 1)
    this.setData({ marketImages })
  },

  openOrderIntent() { this.setData({ showOrder: true }) },
  closeOrder() { this.setData({ showOrder: false }) },
  submitOrderIntent(e) {
    const { item, budget, desc } = e.detail.value
    if (!item || !budget || !desc) return wx.showToast({ title: '请完整填写意向发布', icon: 'none' })
    const orderIntents = [{
      id: Date.now(),
      item,
      budget,
      desc,
      owner: this.data.userInfo.nickName || '发布同学'
    }, ...this.data.orderIntents]
    this.setData({ orderIntents, showOrder: false })
    wx.showToast({ title: '意向已发布' })
  },

  // --- Runner ---
  openRunner() { this.setData({ showRunner: true }) },
  closeRunner() { this.setData({ showRunner: false }) },
  submitRunner(e) {
    const { taskType, route, detail } = e.detail.value
    if (!taskType || !route || !detail) return wx.showToast({ title: '请完整填写跑腿信息', icon: 'none' })
    const newPost = {
      id: Date.now(),
      avatarColor: 'orange',
      name: this.data.userInfo.nickName || '发布同学',
      time: '刚刚 · 校园跑腿',
      content: `【${taskType}】${route}`,
      detail: `任务类型：${taskType}\n取送地点：${route}\n任务详情：${detail}`,
      likes: 0,
      comments: 0,
      category: '学习互助',
      commentList: []
    }
    const posts = [newPost, ...this.data.posts]
    this.setData({ posts })
    this.applyCategory(this.data.activeCategory, posts)
    wx.showToast({ title: '跑腿已发布' })
    this.setData({ showRunner: false })
    this.addPoints(4)
  },

  // --- Map ---
  openMap() { this.setData({ showMap: true }) },
  closeMap() { this.setData({ showMap: false }) },
  onRouteInput(e) {
    this.setData({ routeInput: (e.detail && e.detail.value) || '' })
  },
  planRoute() {
    const dest = (this.data.routeInput || '').trim()
    if (!dest) return wx.showToast({ title: '请输入目的地', icon: 'none' })
    this.setData({ routeHint: `已为您规划到 ${dest} 的最优步行路线 · 预计 8 分钟` })
    wx.showToast({ title: '路线已生成' })
  },

  // --- Recruit ---
  openRecruit() { this.setData({ showRecruit: true }) },
  closeRecruit() { this.setData({ showRecruit: false }) },
  submitRecruit(e) {
    const { title, size, intro } = e.detail.value
    if (!title || !size || !intro) return wx.showToast({ title: '请完整填写招募信息', icon: 'none' })
    const newPost = {
      id: Date.now(),
      avatarColor: 'cyan',
      name: this.data.userInfo.nickName || '发布同学',
      time: '刚刚 · 搭子招募',
      content: `${title}（${size}人）`,
      detail: `标题：${title}\n人数：${size}\n介绍：${intro}`,
      likes: 0,
      comments: 0,
      category: '兴趣爱好',
      commentList: []
    }
    const posts = [newPost, ...this.data.posts]
    this.setData({ posts })
    this.applyCategory(this.data.activeCategory, posts)
    wx.showToast({ title: '招募已发布' })
    this.setData({ showRecruit: false })
    this.addPoints(4)
  },

  // --- Chat ---
  openRoom(e) {
    const roomId = Number(e.currentTarget.dataset.id)
    const name = e.currentTarget.dataset.name
    const chatItems = this.data.chatItems.map(item => {
      if (item.id !== roomId) return item
      return { ...item, tag: '已读' }
    })
    this.setData({ showRoom: true, roomTitle: name, roomPeerName: name, roomSelfName: this.data.userInfo.nickName || '我' })
    this.setData({ chatItems })
    this.syncUnreadCount(chatItems)
    this.applyChatFilter(this.data.chatFilter, chatItems)
  },
  closeRoom() { this.setData({ showRoom: false }) },
  
  sendMsg(e) {
    const text = ((e && e.detail && typeof e.detail.value === 'string' ? e.detail.value : this.data.msgInput) || '').trim()
    if (!text) return
    const msgs = this.data.chatMessages.slice()
    msgs.push({ sender: this.data.roomSelfName || this.data.userInfo.nickName || '我', text, isMe: true })
    this.setData({ chatMessages: msgs, msgInput: '' })
  },
  
  openGroup() { this.setData({ showGroup: true, groupAvatar: '' }) },
  closeGroup() { this.setData({ showGroup: false }) },
  chooseGroupAvatar() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      success: (res) => {
        const file = res.tempFiles && res.tempFiles[0] ? res.tempFiles[0].tempFilePath : ''
        this.setData({ groupAvatar: file })
      }
    })
  },
  submitGroup(e) {
    const name = ((e && e.detail && e.detail.value && e.detail.value.name) || '').trim()
    if (!name) return wx.showToast({ title: '请输入群名称', icon: 'none' })
    const newGroup = {
      id: Date.now(),
      name,
      msg: '新群聊已创建',
      tag: '未读 1',
      source: '即时消息',
      roomType: '群聊',
      color: 'linear-gradient(135deg,#7ef0c6,#7aa3ff)',
      avatarImage: this.data.groupAvatar || ''
    }
    this.setData({
      chatItems: [newGroup, ...this.data.chatItems],
      showGroup: false,
      groupAvatar: ''
    })
    this.applyChatFilter(this.data.chatFilter, [newGroup, ...this.data.chatItems])
    this.syncUnreadCount()
    wx.showToast({ title: '群聊已创建' })
  },

  selectChatFilter(e) {
    this.applyChatFilter(e.currentTarget.dataset.filter)
  },
  applyChatFilter(filter, sourceItems) {
    const chatItems = sourceItems || this.data.chatItems
    const filteredChatItems = chatItems.filter(item => {
      if (filter === '全部') return true
      if (filter === '圈子') return item.source === '圈子消息'
      if (filter === '集市') return item.source === '集市消息'
      if (filter === '评分') return item.source === '评分消息'
      if (filter === '群聊') return item.roomType === '群聊'
      return true
    })
    this.setData({ chatFilter: filter, filteredChatItems })
  },

  onCommentInput(e) {
    this.setData({ commentInput: e.detail.value || '' })
  },

  onMsgInput(e) {
    this.setData({ msgInput: e.detail.value || '' })
  },

  // --- Profile & Settings ---
  openSettings() { this.setData({ showSettings: true }) },
  closeSettings() { this.setData({ showSettings: false }) },
  toggleTheme() {
    const next = this.data.theme === 'dark' ? 'light' : 'dark'
    this.setData({ theme: next })
    wx.showToast({ title: next === 'light' ? '已切换浅色' : '已切换深色', icon: 'none' })
  },
  openMyPosts() {
    this.setData({ showMyPosts: true, myPublishTab: '圈子' })
  },
  closeMyPosts() {
    this.setData({ showMyPosts: false })
  },
  selectMyPublishTab(e) {
    this.setData({ myPublishTab: e.currentTarget.dataset.tab })
  },
  openMyPublishDetail(e) {
    const id = Number(e.currentTarget.dataset.id)
    const type = e.currentTarget.dataset.type
    this.setData({ showMyPosts: false })
    if (type === 'post') {
      const post = this.data.posts.find(item => item.id === id)
      if (!post) return
      this.openDetail({ currentTarget: { dataset: { id: post.id, type: 'post', title: post.content, contact: post.name } } })
      return
    }
    if (type === 'market') {
      const market = this.data.marketItems.find(item => item.id === id)
      if (!market) return
      this.openDetail({ currentTarget: { dataset: { id: market.id, type: 'market', title: market.title, contact: market.owner } } })
      return
    }
    if (type === 'intent') {
      const intent = this.data.orderIntents.find(item => item.id === id)
      if (!intent) return
      this.openDetail({ currentTarget: { dataset: { id: intent.id, type: 'intent', title: `求购：${intent.item}`, contact: intent.owner } } })
    }
  },
  editMyPublish() {
    wx.showToast({ title: '编辑功能开发中', icon: 'none' })
  },
  removeMyPublish(e) {
    const id = Number(e.currentTarget.dataset.id)
    const type = e.currentTarget.dataset.type
    if (type === 'post') {
      const posts = this.data.posts.filter(item => item.id !== id)
      this.setData({ posts, postsCount: posts.length })
      this.applyCategory(this.data.activeCategory, posts)
    } else if (type === 'market') {
      const marketItems = this.data.marketItems.filter(item => item.id !== id)
      this.setData({ marketItems, goodsCount: marketItems.length })
    } else if (type === 'intent') {
      const orderIntents = this.data.orderIntents.filter(item => item.id !== id)
      this.setData({ orderIntents })
    }
    wx.showToast({ title: '已下架', icon: 'none' })
  },
  openFaq() {
    wx.showToast({ title: '客服功能开发中', icon: 'none' })
  },
  syncUnreadCount(sourceItems) {
    const chatItems = sourceItems || this.data.chatItems
    const unreadCount = chatItems.reduce((sum, item) => {
      const match = (item.tag || '').match(/未读\s*(\d+)/)
      return sum + (match ? Number(match[1]) : 0)
    }, 0)
    this.setData({ unreadCount })
  },
  onDndChange(e) {
    this.setData({ dnd: !!(e.detail && e.detail.value) })
  },
  onMarketingChange(e) {
    this.setData({ marketingOff: !!(e.detail && e.detail.value) })
  },
  setTextSize(e) {
    const size = e.currentTarget.dataset.size
    this.setData({ textSize: size })
  },
  toggleInterest(e) {
    const tag = e.currentTarget.dataset.tag
    const selectedInterests = this.data.selectedInterests.slice()
    const index = selectedInterests.indexOf(tag)
    if (index > -1) {
      selectedInterests.splice(index, 1)
    } else {
      selectedInterests.push(tag)
    }
    this.setData({ selectedInterests })
  },
  onCustomInterestInput(e) {
    this.setData({ customInterestInput: (e.detail && e.detail.value) || '' })
  },
  addCustomInterest() {
    const tag = (this.data.customInterestInput || '').trim()
    if (!tag) return
    if (this.data.interests.includes(tag)) return this.setData({ customInterestInput: '' })
    this.setData({
      interests: [...this.data.interests, tag],
      selectedInterests: [...this.data.selectedInterests, tag],
      customInterestInput: ''
    })
  },
  removeInterest(e) {
    const tag = e.currentTarget.dataset.tag
    const interests = this.data.interests.filter(item => item !== tag)
    const selectedInterests = this.data.selectedInterests.filter(item => item !== tag)
    this.setData({ interests, selectedInterests })
  },
  
  openSchool() { this.setData({ showSchool: true }) },
  closeSchool() { this.setData({ showSchool: false }) },
  chooseSchool(e) {
    this.setData({ school: e.currentTarget.dataset.school, showSchool: false })
    wx.showToast({ title: '已切换校区' })
  },

  addPoints(n) {
    this.setData({ points: this.data.points + n })
  }
})
