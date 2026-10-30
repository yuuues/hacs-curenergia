const t=globalThis,e=t.ShadowRoot&&(void 0===t.ShadyCSS||t.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,i=Symbol(),s=new WeakMap;let r=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==i)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o;const i=this.t;if(e&&void 0===t){const e=void 0!==i&&1===i.length;e&&(t=s.get(i)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&s.set(i,t))}return t}toString(){return this.cssText}};const a=(t,...e)=>{const s=1===t.length?t[0]:e.reduce((e,i,s)=>e+(t=>{if(!0===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+t[s+1],t[0]);return new r(s,t,i)},o=e?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const i of t.cssRules)e+=i.cssText;return(t=>new r("string"==typeof t?t:t+"",void 0,i))(e)})(t):t,{is:n,defineProperty:l,getOwnPropertyDescriptor:c,getOwnPropertyNames:d,getOwnPropertySymbols:h,getPrototypeOf:p}=Object,u=globalThis,_=u.trustedTypes,m=_?_.emptyScript:"",g=u.reactiveElementPolyfillSupport,v=(t,e)=>t,$={toAttribute(t,e){switch(e){case Boolean:t=t?m:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t)}return t},fromAttribute(t,e){let i=t;switch(e){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t)}catch(t){i=null}}return i}},y=(t,e)=>!n(t,e),f={attribute:!0,type:String,converter:$,reflect:!1,useDefault:!1,hasChanged:y};Symbol.metadata??=Symbol("metadata"),u.litPropertyMetadata??=new WeakMap;let b=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=f){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){const i=Symbol(),s=this.getPropertyDescriptor(t,i,e);void 0!==s&&l(this.prototype,t,s)}}static getPropertyDescriptor(t,e,i){const{get:s,set:r}=c(this.prototype,t)??{get(){return this[e]},set(t){this[e]=t}};return{get:s,set(e){const a=s?.call(this);r?.call(this,e),this.requestUpdate(t,a,i)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??f}static _$Ei(){if(this.hasOwnProperty(v("elementProperties")))return;const t=p(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(v("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(v("properties"))){const t=this.properties,e=[...d(t),...h(t)];for(const i of e)this.createProperty(i,t[i])}const t=this[Symbol.metadata];if(null!==t){const e=litPropertyMetadata.get(t);if(void 0!==e)for(const[t,i]of e)this.elementProperties.set(t,i)}this._$Eh=new Map;for(const[t,e]of this.elementProperties){const i=this._$Eu(t,e);void 0!==i&&this._$Eh.set(i,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){const e=[];if(Array.isArray(t)){const i=new Set(t.flat(1/0).reverse());for(const t of i)e.unshift(o(t))}else void 0!==t&&e.push(o(t));return e}static _$Eu(t,e){const i=e.attribute;return!1===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){const t=new Map,e=this.constructor.elementProperties;for(const i of e.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t)}createRenderRoot(){const i=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return((i,s)=>{if(e)i.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const e of s){const s=document.createElement("style"),r=t.litNonce;void 0!==r&&s.setAttribute("nonce",r),s.textContent=e.cssText,i.appendChild(s)}})(i,this.constructor.elementStyles),i}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,i){this._$AK(t,i)}_$ET(t,e){const i=this.constructor.elementProperties.get(t),s=this.constructor._$Eu(t,i);if(void 0!==s&&!0===i.reflect){const r=(void 0!==i.converter?.toAttribute?i.converter:$).toAttribute(e,i.type);this._$Em=t,null==r?this.removeAttribute(s):this.setAttribute(s,r),this._$Em=null}}_$AK(t,e){const i=this.constructor,s=i._$Eh.get(t);if(void 0!==s&&this._$Em!==s){const t=i.getPropertyOptions(s),r="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:$;this._$Em=s;const a=r.fromAttribute(e,t.type);this[s]=a??this._$Ej?.get(s)??a,this._$Em=null}}requestUpdate(t,e,i,s=!1,r){if(void 0!==t){const a=this.constructor;if(!1===s&&(r=this[t]),i??=a.getPropertyOptions(t),!((i.hasChanged??y)(r,e)||i.useDefault&&i.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(a._$Eu(t,i))))return;this.C(t,e,i)}!1===this.isUpdatePending&&(this._$ES=this._$EP())}C(t,e,{useDefault:i,reflect:s,wrapped:r},a){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,a??e??this[t]),!0!==r||void 0!==a)||(this._$AL.has(t)||(this.hasUpdated||i||(e=void 0),this._$AL.set(t,e)),!0===s&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,e]of this._$Ep)this[t]=e;this._$Ep=void 0}const t=this.constructor.elementProperties;if(t.size>0)for(const[e,i]of t){const{wrapped:t}=i,s=this[e];!0!==t||this._$AL.has(e)||void 0===s||this.C(e,void 0,i,s)}}let t=!1;const e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(e){throw t=!1,this._$EM(),e}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(t){}firstUpdated(t){}};b.elementStyles=[],b.shadowRootOptions={mode:"open"},b[v("elementProperties")]=new Map,b[v("finalized")]=new Map,g?.({ReactiveElement:b}),(u.reactiveElementVersions??=[]).push("2.1.2");const x=globalThis,w=t=>t,A=x.trustedTypes,k=A?A.createPolicy("lit-html",{createHTML:t=>t}):void 0,E="$lit$",C=`lit$${Math.random().toFixed(9).slice(2)}$`,S="?"+C,P=`<${S}>`,M=document,I=()=>M.createComment(""),U=t=>null===t||"object"!=typeof t&&"function"!=typeof t,N=Array.isArray,O="[ \t\n\f\r]",T=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,R=/-->/g,H=/>/g,D=RegExp(`>|${O}(?:([^\\s"'>=/]+)(${O}*=${O}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),z=/'/g,W=/"/g,L=/^(?:script|style|textarea|title)$/i,q=t=>(e,...i)=>({_$litType$:t,strings:e,values:i}),j=q(1),F=q(2),B=Symbol.for("lit-noChange"),V=Symbol.for("lit-nothing"),K=new WeakMap,G=M.createTreeWalker(M,129);function J(t,e){if(!N(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==k?k.createHTML(e):e}const Z=(t,e)=>{const i=t.length-1,s=[];let r,a=2===e?"<svg>":3===e?"<math>":"",o=T;for(let e=0;e<i;e++){const i=t[e];let n,l,c=-1,d=0;for(;d<i.length&&(o.lastIndex=d,l=o.exec(i),null!==l);)d=o.lastIndex,o===T?"!--"===l[1]?o=R:void 0!==l[1]?o=H:void 0!==l[2]?(L.test(l[2])&&(r=RegExp("</"+l[2],"g")),o=D):void 0!==l[3]&&(o=D):o===D?">"===l[0]?(o=r??T,c=-1):void 0===l[1]?c=-2:(c=o.lastIndex-l[2].length,n=l[1],o=void 0===l[3]?D:'"'===l[3]?W:z):o===W||o===z?o=D:o===R||o===H?o=T:(o=D,r=void 0);const h=o===D&&t[e+1].startsWith("/>")?" ":"";a+=o===T?i+P:c>=0?(s.push(n),i.slice(0,c)+E+i.slice(c)+C+h):i+C+(-2===c?e:h)}return[J(t,a+(t[i]||"<?>")+(2===e?"</svg>":3===e?"</math>":"")),s]};class Y{constructor({strings:t,_$litType$:e},i){let s;this.parts=[];let r=0,a=0;const o=t.length-1,n=this.parts,[l,c]=Z(t,e);if(this.el=Y.createElement(l,i),G.currentNode=this.el.content,2===e||3===e){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes)}for(;null!==(s=G.nextNode())&&n.length<o;){if(1===s.nodeType){if(s.hasAttributes())for(const t of s.getAttributeNames())if(t.endsWith(E)){const e=c[a++],i=s.getAttribute(t).split(C),o=/([.?@])?(.*)/.exec(e);n.push({type:1,index:r,name:o[2],strings:i,ctor:"."===o[1]?it:"?"===o[1]?st:"@"===o[1]?rt:et}),s.removeAttribute(t)}else t.startsWith(C)&&(n.push({type:6,index:r}),s.removeAttribute(t));if(L.test(s.tagName)){const t=s.textContent.split(C),e=t.length-1;if(e>0){s.textContent=A?A.emptyScript:"";for(let i=0;i<e;i++)s.append(t[i],I()),G.nextNode(),n.push({type:2,index:++r});s.append(t[e],I())}}}else if(8===s.nodeType)if(s.data===S)n.push({type:2,index:r});else{let t=-1;for(;-1!==(t=s.data.indexOf(C,t+1));)n.push({type:7,index:r}),t+=C.length-1}r++}}static createElement(t,e){const i=M.createElement("template");return i.innerHTML=t,i}}function Q(t,e,i=t,s){if(e===B)return e;let r=void 0!==s?i._$Co?.[s]:i._$Cl;const a=U(e)?void 0:e._$litDirective$;return r?.constructor!==a&&(r?._$AO?.(!1),void 0===a?r=void 0:(r=new a(t),r._$AT(t,i,s)),void 0!==s?(i._$Co??=[])[s]=r:i._$Cl=r),void 0!==r&&(e=Q(t,r._$AS(t,e.values),r,s)),e}class X{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:e},parts:i}=this._$AD,s=(t?.creationScope??M).importNode(e,!0);G.currentNode=s;let r=G.nextNode(),a=0,o=0,n=i[0];for(;void 0!==n;){if(a===n.index){let e;2===n.type?e=new tt(r,r.nextSibling,this,t):1===n.type?e=new n.ctor(r,n.name,n.strings,this,t):6===n.type&&(e=new at(r,this,t)),this._$AV.push(e),n=i[++o]}a!==n?.index&&(r=G.nextNode(),a++)}return G.currentNode=M,s}p(t){let e=0;for(const i of this._$AV)void 0!==i&&(void 0!==i.strings?(i._$AI(t,i,e),e+=i.strings.length-2):i._$AI(t[e])),e++}}class tt{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,i,s){this.type=2,this._$AH=V,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=i,this.options=s,this._$Cv=s?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode;const e=this._$AM;return void 0!==e&&11===t?.nodeType&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=Q(this,t,e),U(t)?t===V||null==t||""===t?(this._$AH!==V&&this._$AR(),this._$AH=V):t!==this._$AH&&t!==B&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):(t=>N(t)||"function"==typeof t?.[Symbol.iterator])(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==V&&U(this._$AH)?this._$AA.nextSibling.data=t:this.T(M.createTextNode(t)),this._$AH=t}$(t){const{values:e,_$litType$:i}=t,s="number"==typeof i?this._$AC(t):(void 0===i.el&&(i.el=Y.createElement(J(i.h,i.h[0]),this.options)),i);if(this._$AH?._$AD===s)this._$AH.p(e);else{const t=new X(s,this),i=t.u(this.options);t.p(e),this.T(i),this._$AH=t}}_$AC(t){let e=K.get(t.strings);return void 0===e&&K.set(t.strings,e=new Y(t)),e}k(t){N(this._$AH)||(this._$AH=[],this._$AR());const e=this._$AH;let i,s=0;for(const r of t)s===e.length?e.push(i=new tt(this.O(I()),this.O(I()),this,this.options)):i=e[s],i._$AI(r),s++;s<e.length&&(this._$AR(i&&i._$AB.nextSibling,s),e.length=s)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){const e=w(t).nextSibling;w(t).remove(),t=e}}setConnected(t){void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t))}}class et{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,i,s,r){this.type=1,this._$AH=V,this._$AN=void 0,this.element=t,this.name=e,this._$AM=s,this.options=r,i.length>2||""!==i[0]||""!==i[1]?(this._$AH=Array(i.length-1).fill(new String),this.strings=i):this._$AH=V}_$AI(t,e=this,i,s){const r=this.strings;let a=!1;if(void 0===r)t=Q(this,t,e,0),a=!U(t)||t!==this._$AH&&t!==B,a&&(this._$AH=t);else{const s=t;let o,n;for(t=r[0],o=0;o<r.length-1;o++)n=Q(this,s[i+o],e,o),n===B&&(n=this._$AH[o]),a||=!U(n)||n!==this._$AH[o],n===V?t=V:t!==V&&(t+=(n??"")+r[o+1]),this._$AH[o]=n}a&&!s&&this.j(t)}j(t){t===V?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}}class it extends et{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===V?void 0:t}}class st extends et{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==V)}}class rt extends et{constructor(t,e,i,s,r){super(t,e,i,s,r),this.type=5}_$AI(t,e=this){if((t=Q(this,t,e,0)??V)===B)return;const i=this._$AH,s=t===V&&i!==V||t.capture!==i.capture||t.once!==i.once||t.passive!==i.passive,r=t!==V&&(i===V||s);s&&this.element.removeEventListener(this.name,this,i),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}}class at{constructor(t,e,i){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=i}get _$AU(){return this._$AM._$AU}_$AI(t){Q(this,t)}}const ot=x.litHtmlPolyfillSupport;ot?.(Y,tt),(x.litHtmlVersions??=[]).push("3.3.3");const nt=globalThis;class lt extends b{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=((t,e,i)=>{const s=i?.renderBefore??e;let r=s._$litPart$;if(void 0===r){const t=i?.renderBefore??null;s._$litPart$=r=new tt(e.insertBefore(I(),t),t,void 0,i??{})}return r._$AI(t),r})(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return B}}lt._$litElement$=!0,lt.finalized=!0,nt.litElementHydrateSupport?.({LitElement:lt});const ct=nt.litElementPolyfillSupport;ct?.({LitElement:lt}),(nt.litElementVersions??=[]).push("4.2.2");const dt="—";function ht(t,e,i,s){const r={minimumFractionDigits:i,maximumFractionDigits:s};let a;try{a=new Intl.NumberFormat(t,r)}catch(t){if(!(t instanceof RangeError))throw t;a=new Intl.NumberFormat("en",r)}return a.format(e).replace(/[  ]/g," ")}function pt(t){const e=/^(\d{4})-(\d{2})-(\d{2})/.exec(t);return e?`${e[3]}/${e[2]}/${e[1]}`:t}function ut(t,e){return null===e?dt:`${ht(t,e,0,2)} kWh`}function _t(t,e){return null===e?dt:`${ht(t,e,2,2)} €`}function mt(t,e){return null===e?dt:`${ht(t,e,4,4)} €/kWh`}function gt(t,e){return null===e?dt:`${ht(t,e,1,1)} %`}function vt(t,e,i){if(null===e)return dt;const s="kwh"===i?"kWh":"€",r="kwh"===i?[0,2]:[2,2],a=ht(t,Math.abs(e),...r);return`${0===Number(Math.abs(e).toFixed(r[1]))?"":e<0?"−":"+"}${a} ${s}`}function $t(t,e){return null===e?dt:`${ht(t,e,0,2)} %`}const yt={es:{pill_estimated:"estimada",pill_unreadable:"no se pudo leer",tab_electricity:"Luz",tab_gas:"Gas",col_period:"Periodo",col_kwh_invoice:"kWh factura",col_kwh_edata:"kWh Datadis",col_delta_kwh:"Δ kWh",col_amount:"Importe",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Potencia + energía: factura {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_group:"Comparada junto con: {numbers}",detail_in_group_of:"Regularizada en la factura {number}",detail_vat:"IVA {rate} sobre {base}: {amount}",detail_energy_price:"Precio de la energía: {price}",detail_period_row:"{period}: factura {invoice} / Datadis {edata}",row_covers:"abarca {n} facturas",detail_own_kwh:"Esta factura: {kwh}",detail_group_heading:"Comparación del grupo ({n} facturas)",card_title:"Facturas",loading:"Cargando…",empty:"Todavía no hay facturas",error:"No se pudieron cargar las facturas",card_description:"Facturas de CurEnergía comparadas con los datos de Datadis",chart_title:"kWh por factura",chart_empty:"Sin datos para el gráfico",chart_invoice:"Factura",chart_datadis:"Datadis",panel_title:"Facturas",panel_billed_12m:"Facturado en 12 meses",panel_kwh_delta:"kWh factura vs Datadis",panel_estimated_count:"Lecturas estimadas",panel_unreadable:"{n} correos con factura que no se pudo leer",panel_unsupported:"Correos con factura no soportada (rectificativa o abono): {n}",panel_mail_error:"No se pudo leer el correo; se muestran las facturas guardadas",editor_title:"Título",editor_supply:"Pestaña inicial",editor_max_invoices:"Número máximo de facturas",editor_entry_id:"Cuenta de correo (opcional)"},en:{pill_estimated:"estimated",pill_unreadable:"could not be read",tab_electricity:"Electricity",tab_gas:"Gas",col_period:"Period",col_kwh_invoice:"Invoice kWh",col_kwh_edata:"Datadis kWh",col_delta_kwh:"Δ kWh",col_amount:"Amount",col_delta_eur:"Δ €",col_kwh:"kWh",col_m3:"m³",col_price_kwh:"€/kWh",detail_power_energy:"Power + energy: invoice {invoice} / e-data {edata}",detail_delta_pct:"Δ {pct}",detail_group:"Compared together with: {numbers}",detail_in_group_of:"Settled by invoice {number}",detail_vat:"VAT {rate} on {base}: {amount}",detail_energy_price:"Energy price: {price}",detail_period_row:"{period}: invoice {invoice} / Datadis {edata}",row_covers:"covers {n} invoices",detail_own_kwh:"This invoice: {kwh}",detail_group_heading:"Group comparison ({n} invoices)",card_title:"Invoices",loading:"Loading…",empty:"No invoices yet",error:"Could not load the invoices",card_description:"CurEnergía invoices compared with Datadis data",chart_title:"kWh per invoice",chart_empty:"No data for the chart",chart_invoice:"Invoice",chart_datadis:"Datadis",panel_title:"Invoices",panel_billed_12m:"Billed in 12 months",panel_kwh_delta:"Invoice kWh vs Datadis",panel_estimated_count:"Estimated readings",panel_unreadable:"{n} e-mails with an invoice could not be read",panel_unsupported:"E-mails with an unsupported invoice (corrective or credit note): {n}",panel_mail_error:"Could not read the mailbox; showing the saved invoices",editor_title:"Title",editor_supply:"Initial tab",editor_max_invoices:"Maximum number of invoices",editor_entry_id:"Mail account (optional)"}};function ft(t){return t.locale?.language||t.language||"en"}function bt(t,e,i){const s=(ft(t).toLowerCase().startsWith("es")?yt.es:yt.en)[e];return i?s.replace(/\{(\w+)\}/g,(t,e)=>e in i?String(i[e]):t):s}const xt=[{supply:"electricity",label:"tab_electricity"},{supply:"gas",label:"tab_gas"}],wt=[{key:"p1",name:"P1"},{key:"p2",name:"P2"},{key:"p3",name:"P3"}];function At(t,e){return e.period_end.localeCompare(t.period_end)||e.issue_date.localeCompare(t.issue_date)||e.number.localeCompare(t.number)}class kt extends lt{constructor(){super(),this.contracts=[],this.supply="electricity",this._expanded=new Set}render(){const t=(this.contracts??[]).filter(t=>t.supply===this.supply);return j`
      <div class="tabs" role="tablist">
        ${xt.map(({supply:t,label:e})=>j`
            <button
              class="tab"
              role="tab"
              type="button"
              aria-selected=${t===this.supply?"true":"false"}
              @click=${()=>this._selectSupply(t)}
            >
              ${bt(this.hass,e)}
            </button>
          `)}
      </div>
      ${0===t.length?j`<div class="empty">${bt(this.hass,"empty")}</div>`:t.map(e=>this._renderContract(e,t.length>1))}
    `}_renderContract(t,e){const i=[...t.invoices].sort(At),s=this.maxInvoices,r=s&&s>0?i.slice(0,s):i,a="gas"===this.supply?["col_period","col_kwh","col_m3","col_amount","col_price_kwh"]:["col_period","col_kwh_invoice","col_kwh_edata","col_delta_kwh","col_amount","col_delta_eur"];return j`
      ${e?j`<h3 class="contract-name">${t.name}</h3>`:V}
      <div class="scroll">
        <table>
          <thead>
            <tr>
              ${a.map(t=>j`<th>${bt(this.hass,t)}</th>`)}
            </tr>
          </thead>
          <tbody>
            ${r.map(e=>this._renderRow(t,e,a.length))}
          </tbody>
        </table>
      </div>
    `}_renderRow(t,e,i){const s=ft(this.hass),r=`${t.entry_id}|${t.contract}|${e.number}`,a=this._expanded.has(r),o=e.comparison?.group.length??0,n=`color: var(${function(t){switch(t){case"ok":return"--success-color";case"no_cuadra":return"--warning-color";case"no_leida":return"--error-color";default:return"--secondary-text-color"}}(e.status)})`,l=()=>this._toggle(r),c=j`
      <td>
        ${function(t,e){const i=pt(t),s=pt(e);return t.slice(0,4)===e.slice(0,4)?`${i.slice(0,5)} – ${s}`:`${i} – ${s}`}(e.period_start,e.period_end)}
        ${e.estimated?j`<span class="pill">${bt(this.hass,"pill_estimated")}</span>`:V}
        ${"no_leida"===e.status?j`<span class="pill error">${bt(this.hass,"pill_unreadable")}</span>`:V}
        ${o>1?j`<span class="note">${bt(this.hass,"row_covers",{n:o})}</span>`:V}
      </td>
    `,d=e.comparison,h="gas"===e.supply?j`
            <td>${ut(s,e.kwh)}</td>
            <td>${function(t,e){return null===e?dt:`${ht(t,e,0,2)} m³`}(s,e.m3)}</td>
            <td>${_t(s,e.total)}</td>
            <td>${mt(s,e.price_kwh)}</td>
          `:j`
            <td>${ut(s,d?.invoice_kwh??e.kwh)}</td>
            <td>${ut(s,d?.edata_kwh??null)}</td>
            <td style=${n}>${vt(s,d?.delta_kwh??null,"kwh")}</td>
            <td>${_t(s,e.total)}</td>
            <td style=${n}>${vt(s,d?.delta_eur??null,"eur")}</td>
          `;return j`
      <tr
        class="row ${e.estimated?"estimated":""}"
        tabindex="0"
        aria-expanded=${a?"true":"false"}
        @click=${l}
        @keydown=${t=>{"Enter"!==t.key&&" "!==t.key||(t.preventDefault(),l())}}
      >
        ${c} ${h}
      </tr>
      ${a?j`<tr class="detail">
            <td colspan=${i}>${this._renderDetail(e)}</td>
          </tr>`:V}
    `}_renderDetail(t){const e=ft(this.hass),i="gas"!==t.supply,s=t.comparison;return j`
      <div class="detail-body">
        <ul>
          ${t.concepts.map(t=>j`<li><span>${t.label}</span><span>${_t(e,t.amount)}</span></li>`)}
        </ul>
        <div>
          ${bt(this.hass,"detail_vat",{rate:$t(e,t.vat.rate),base:_t(e,t.vat.base),amount:_t(e,t.vat.amount)})}
        </div>
        ${i?this._renderElectricityDetail(t,s):V}
        ${t.in_group_of?j`<div>
              ${bt(this.hass,"detail_in_group_of",{number:t.in_group_of})}
            </div>`:V}
        ${s&&s.group.length>1?j`<div>
              ${bt(this.hass,"detail_group",{numbers:s.group.join(", ")})}
            </div>`:V}
      </div>
    `}_renderElectricityDetail(t,e){const i=ft(this.hass),s=e?.invoice_periods??t.periods,r=e?.edata_periods??null,a=null!==s||null!==r,o=(e?.group.length??0)>1;return j`
      ${o?j`<div>${bt(this.hass,"detail_own_kwh",{kwh:ut(i,t.kwh)})}</div>
            <strong>
              ${bt(this.hass,"detail_group_heading",{n:e?.group.length??0})}
            </strong>`:V}
      ${a?j`<ul>
            ${wt.map(({key:t,name:e})=>j`<li>
                  ${bt(this.hass,"detail_period_row",{period:e,invoice:ut(i,s?.[t]??null),edata:ut(i,r?.[t]??null)})}
                </li>`)}
          </ul>`:V}
      ${e?j`<div>
            ${bt(this.hass,"detail_power_energy",{invoice:_t(i,e.invoice_eur),edata:_t(i,e.edata_eur)})}
            (${bt(this.hass,"detail_delta_pct",{pct:gt(i,e.delta_pct)})})
          </div>`:V}
      <div>
        ${bt(this.hass,"detail_energy_price",{price:mt(i,t.energy_price_kwh)})}
      </div>
    `}_toggle(t){const e=new Set(this._expanded);e.delete(t)||e.add(t),this._expanded=e}_selectSupply(t){t!==this.supply&&(this.supply=t,this._expanded=new Set,this.dispatchEvent(new CustomEvent("supply-changed",{detail:{supply:t},bubbles:!0,composed:!0})))}}kt.properties={hass:{attribute:!1},contracts:{attribute:!1},supply:{type:String},maxInvoices:{type:Number,attribute:"max-invoices"},_expanded:{state:!0}},kt.styles=a`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .tabs {
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--divider-color);
      margin-bottom: 8px;
    }
    .tab {
      appearance: none;
      background: none;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--secondary-text-color);
      cursor: pointer;
      font: inherit;
      padding: 8px 12px;
    }
    .tab[aria-selected="true"] {
      border-bottom-color: var(--primary-color);
      color: var(--primary-text-color);
      font-weight: 500;
    }
    .contract-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 12px 0 4px;
    }
    .scroll {
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      width: 100%;
    }
    th,
    td {
      padding: 8px 6px;
      text-align: right;
      white-space: nowrap;
    }
    th:first-child,
    td:first-child {
      text-align: left;
    }
    th {
      border-bottom: 1px solid var(--divider-color);
      color: var(--secondary-text-color);
      font-weight: 500;
    }
    tr.row {
      cursor: pointer;
    }
    tr.row:hover,
    tr.row:focus-visible {
      background: var(--secondary-background-color, transparent);
    }
    tr.row:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: -2px;
    }
    tr.row td {
      border-bottom: 1px solid var(--divider-color);
    }
    tr.row.estimated {
      color: var(--secondary-text-color);
    }
    .pill {
      border: 1px solid var(--divider-color);
      border-radius: 10px;
      color: var(--secondary-text-color);
      font-size: 0.8em;
      margin-left: 6px;
      padding: 1px 6px;
    }
    .pill.error {
      border-color: var(--error-color);
      color: var(--error-color);
    }
    .note {
      color: var(--secondary-text-color);
      display: block;
      font-size: 0.85em;
    }
    tr.detail td {
      background: var(--secondary-background-color, transparent);
      border-bottom: 1px solid var(--divider-color);
      text-align: left;
      white-space: normal;
    }
    .detail-body {
      display: grid;
      gap: 6px;
      padding: 4px 0;
    }
    .detail-body ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    .detail-body li {
      display: flex;
      gap: 12px;
      justify-content: space-between;
    }
    .empty {
      color: var(--secondary-text-color);
      padding: 16px 0;
      text-align: center;
    }
    @media (max-width: 450px) {
      th,
      td {
        padding: 6px 4px;
      }
    }
  `,customElements.get("curenergia-invoice-table")||customElements.define("curenergia-invoice-table",kt);const Et={title:"editor_title",supply:"editor_supply",max_invoices:"editor_max_invoices",entry_id:"editor_entry_id"};class Ct extends lt{constructor(){super(...arguments),this._computeLabel=t=>{const e=Et[t.name];return e&&this.hass?bt(this.hass,e):t.name},this._valueChanged=t=>{t.stopPropagation();const e=t.detail.value,i={type:this._config?.type};for(const[t,s]of Object.entries(e))null!=s&&""!==s&&(i[t]=s);void 0===i.type&&delete i.type,this._config=i,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:i},bubbles:!0,composed:!0}))}}setConfig(t){this._config=t}_schema(){const t=this.hass;return[{name:"title",selector:{text:{}}},{name:"supply",selector:{select:{mode:"dropdown",options:[{value:"electricity",label:bt(t,"tab_electricity")},{value:"gas",label:bt(t,"tab_gas")}]}}},{name:"max_invoices",selector:{number:{min:1,max:60,mode:"box"}}},{name:"entry_id",selector:{config_entry:{integration:"curenergia"}}}]}render(){return this.hass&&this._config?j`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${this._schema()}
        .computeLabel=${this._computeLabel}
        @value-changed=${this._valueChanged}
      ></ha-form>
    `:V}}function St(t){return Object.fromEntries(Object.entries(t).filter(([,t])=>void 0!==t))}function Pt(t,e={}){return t.connection.sendMessagePromise(St({type:"curenergia/invoices",entry_id:e.entry_id,supply:e.supply}))}function Mt(t,e){return t.connection.sendMessagePromise(St({type:"curenergia/summary",entry_id:e}))}Ct.properties={hass:{attribute:!1},_config:{state:!0}},customElements.get("curenergia-invoices-card-editor")||customElements.define("curenergia-invoices-card-editor",Ct);class It extends lt{constructor(){super(),this._requestId=0,this._onSupplyChanged=t=>{const e=t.detail?.supply;"electricity"!==e&&"gas"!==e||(this._supply=e)},this._failed=!1,this._supply="electricity"}static getStubConfig(){return{max_invoices:6}}static getConfigElement(){return document.createElement("curenergia-invoices-card-editor")}get hass(){return this._hass}set hass(t){this._hass=t,this.requestUpdate(),this._start()}setConfig(t){const e=function(t){if(null===t||"object"!=typeof t||Array.isArray(t))throw new Error("Invalid configuration");const{max_invoices:e,supply:i,title:s,entry_id:r}=t;if(void 0!==e&&("number"!=typeof e||!Number.isInteger(e)||e<1||e>60))throw new Error("max_invoices must be an integer between 1 and 60");if(void 0!==i&&"electricity"!==i&&"gas"!==i)throw new Error('supply must be "electricity" or "gas"');if(void 0!==s&&"string"!=typeof s)throw new Error("title must be a string");if(void 0!==r&&"string"!=typeof r)throw new Error("entry_id must be a string");return t}(t),i=this._config;this._config=e,this._supply=e.supply??"electricity",i&&i.entry_id!==e.entry_id&&void 0!==this._timer&&this._load()}getCardSize(){const t=this._config?.max_invoices??6,e=(this._data??[]).filter(t=>t.supply===this._supply).reduce((t,e)=>t+e.invoices.length,0);return 3+Math.min(t,e)}connectedCallback(){super.connectedCallback(),this._start()}disconnectedCallback(){super.disconnectedCallback(),this._stop()}_start(){void 0===this._timer&&this.isConnected&&this._hass&&this._config&&(this._timer=setInterval(()=>{this._load()},9e5),this._load())}_stop(){void 0!==this._timer&&clearInterval(this._timer),this._timer=void 0,this._requestId+=1}async _load(){const t=this._hass;if(!t)return;this._requestId+=1;const e=this._requestId;try{const i=await Pt(t,{entry_id:this._config?.entry_id});if(e!==this._requestId)return;this._data=i.contracts??[],this._failed=!1}catch{if(e!==this._requestId)return;this._failed=!0}}render(){const t=this._config,e=this._hass;return t&&e?j`
      <ha-card .header=${t.title??bt(e,"card_title")}>
        <div class="body">
          ${this._failed?j`<div class="message error">${bt(e,"error")}</div>`:V}
          ${void 0===this._data?this._failed?V:j`<div class="message">${bt(e,"loading")}</div>`:j`<curenergia-invoice-table
                .hass=${e}
                .contracts=${this._data}
                .supply=${this._supply}
                .maxInvoices=${t.max_invoices??6}
                @supply-changed=${this._onSupplyChanged}
              ></curenergia-invoice-table>`}
        </div>
      </ha-card>
    `:V}}It.properties={_config:{state:!0},_data:{state:!0},_failed:{state:!0},_supply:{state:!0}},It.styles=a`
    :host {
      display: block;
    }
    ha-card {
      display: block;
    }
    .body {
      padding: 0 16px 16px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `,customElements.get("curenergia-invoices-card")||customElements.define("curenergia-invoices-card",It);const Ut=window.customCards??=[];Ut.some(t=>"curenergia-invoices-card"===t.type)||Ut.push({type:"curenergia-invoices-card",name:"CurEnergía",description:yt.en.card_description,preview:!1,documentationURL:"https://github.com/yuuues/hacs-curenergia#readme"});const Nt=640,Ot=212;function Tt(t){const e=/^(\d{4})-(\d{2})/.exec(t);return e?`${e[2]}/${e[1].slice(2)}`:t}function Rt(t,e){const i=t.comparison;if(!i||null===i.edata_kwh)return null;if(i.group.length<=1)return i.edata_kwh;const s=e.filter(e=>e.in_group_of===t.number),r=i.group.filter(e=>e!==t.number);let a=i.edata_kwh;for(const t of r){const e=s.find(e=>e.number===t),i=e?.comparison?.edata_kwh??null;if(null===i)return null;a-=i}return Math.round(100*a)/100}function Ht(t){return"no_leida"===t.status?"unreadable":t.estimated?"estimated":null}function Dt(t,e){return t.period_end.localeCompare(e.period_end)||t.issue_date.localeCompare(e.issue_date)||t.number.localeCompare(e.number)}class zt extends lt{constructor(){super(),this.invoices=[]}_points(){const t=this.invoices.filter(t=>"electricity"===t.supply);return[...t].sort(Dt).slice(-12).map(e=>({label:Tt(e.period_end),invoice:e.kwh,datadis:Rt(e,t),mark:Ht(e)}))}render(){const t=this.hass;if(!t)return V;const e=ft(t),i=this._points(),s=i.flatMap(t=>[t.invoice,t.datadis].filter(t=>null!==t));if(0===s.length)return j`<div class="message">${bt(t,"chart_empty")}</div>`;const r=Math.max(...s,0),a=568/i.length,o=Math.min(.36*a,26),n=bt(t,"chart_invoice"),l=bt(t,"chart_datadis"),c=(i,s,a,c)=>{const d=(t=>r>0?Math.max(t,0)/r*196:0)(a),h="invoice"===i?n:l,p="invoice"===i?c.mark:null;return F`<rect
        class="bar ${i} ${p??""}"
        x=${s}
        y=${Ot-d}
        width=${o}
        height=${d}
        rx="2"
      ><title>${h} ${c.label}: ${ut(e,a)}${(e=>"estimated"===e?` (${bt(t,"pill_estimated")})`:"unreadable"===e?` (${bt(t,"pill_unreadable")})`:"")(p)}</title></rect>`},d=new Set(i.map(t=>t.mark));return j`
      <div class="title">${bt(t,"chart_title")}</div>
      <svg
        viewBox="0 0 ${Nt} ${236}"
        role="img"
        aria-label=${bt(t,"chart_title")}
        preserveAspectRatio="xMidYMid meet"
      >
        <line class="grid" x1=${64} x2=${632} y1=${16} y2=${16} />
        <line
          class="axis"
          x1=${64}
          x2=${632}
          y1=${Ot}
          y2=${Ot}
        />
        <text class="y-label" x=${58} y=${20} text-anchor="end">${ut(e,r)}</text>
        ${i.map((t,e)=>{const i=64+a*e+a/2,s=null!==t.invoice&&null!==t.datadis;return F`
            ${null!==t.invoice?c("invoice",s?i-o-1:i-o/2,t.invoice,t):V}
            ${null!==t.datadis?c("datadis",null!==t.invoice?i+1:i-o/2,t.datadis,t):V}
            <text class="x-label" x=${i} y=${228} text-anchor="middle">${t.label}</text>
          `})}
      </svg>
      <div class="legend">
        <span><i class="swatch invoice"></i>${n}</span>
        <span><i class="swatch datadis"></i>${l}</span>
        ${d.has("estimated")?j`<span><i class="swatch invoice estimated"></i>${bt(t,"pill_estimated")}</span>`:V}
        ${d.has("unreadable")?j`<span><i class="swatch invoice unreadable"></i>${bt(t,"pill_unreadable")}</span>`:V}
      </div>
    `}}zt.properties={hass:{attribute:!1},invoices:{attribute:!1}},zt.styles=a`
    :host {
      display: block;
      color: var(--primary-text-color);
    }
    .title {
      font-weight: 500;
      margin: 8px 0;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    svg {
      display: block;
      width: 100%;
      height: auto;
    }
    .axis {
      stroke: var(--divider-color);
      stroke-width: 1;
    }
    .grid {
      stroke: var(--divider-color);
      stroke-width: 1;
      stroke-dasharray: 3 3;
    }
    text {
      fill: var(--secondary-text-color);
      font-size: 11px;
    }
    .bar.invoice {
      fill: var(--primary-color);
    }
    .bar.datadis {
      fill: var(--secondary-text-color);
    }
    /* Estimated or unreadable invoice figure: lighter fill and dashed outline. */
    .bar.invoice.estimated,
    .bar.invoice.unreadable {
      fill-opacity: 0.35;
      stroke: var(--primary-color);
      stroke-width: 1.5;
      stroke-dasharray: 3 2;
    }
    .bar.invoice.unreadable {
      stroke: var(--error-color);
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      margin: 4px 0 8px;
      color: var(--secondary-text-color);
      font-size: 0.9em;
    }
    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .swatch {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 2px;
    }
    .swatch.invoice {
      background: var(--primary-color);
    }
    .swatch.datadis {
      background: var(--secondary-text-color);
    }
    .swatch.invoice.estimated,
    .swatch.invoice.unreadable {
      background: transparent;
      border: 1.5px dashed var(--primary-color);
      box-sizing: border-box;
    }
    .swatch.invoice.unreadable {
      border-color: var(--error-color);
    }
  `,customElements.get("curenergia-bar-chart")||customElements.define("curenergia-bar-chart",zt);class Wt extends lt{constructor(){super(),this._requestId=0,this._inFlight=!1,this._onSupplyChanged=t=>{const e=t.detail?.supply;"electricity"!==e&&"gas"!==e||(this._supply=e)},this.narrow=!1,this._failed=!1,this._supply="electricity"}get hass(){return this._hass}set hass(t){this._hass=t,this.requestUpdate(),this._start()}connectedCallback(){super.connectedCallback(),this._start()}disconnectedCallback(){super.disconnectedCallback(),this._stop()}_start(){void 0===this._timer&&this.isConnected&&this._hass&&(this._timer=setInterval(()=>{this._load()},9e5),this._load())}_stop(){void 0!==this._timer&&clearInterval(this._timer),this._timer=void 0,this._requestId+=1,this._inFlight=!1}async _load(){const t=this._hass;if(!t||this._inFlight)return;this._inFlight=!0,this._requestId+=1;const e=this._requestId;try{const[i,s]=await Promise.all([Mt(t),Pt(t)]);if(e!==this._requestId)return;this._summary=i,this._data=s.contracts??[],this._failed=!1}catch{if(e!==this._requestId)return;this._failed=!0}finally{e===this._requestId&&(this._inFlight=!1)}}_renderKpis(t){const e=ft(t),i=this._summary,s=(t,e)=>j`<div class="kpi">
        <div class="value">${e}</div>
        <div class="label">${t}</div>
      </div>`;return j`<div class="kpis">
      ${s(bt(t,"panel_billed_12m"),_t(e,i?.billed_12m??null))}
      ${s(bt(t,"panel_kwh_delta"),function(t,e){if(null===e)return dt;const i=ht(t,Math.abs(e),1,1);return`${0===Number(Math.abs(e).toFixed(1))?"":e<0?"−":"+"}${i} %`}(e,i?.kwh_delta_pct??null))}
      ${s(bt(t,"panel_estimated_count"),i?new Intl.NumberFormat(e).format(i.estimated_count):"—")}
    </div>`}_renderBody(t){if(void 0===this._data)return this._failed?j``:j`<div class="message">${bt(t,"loading")}</div>`;if(0===this._data.length)return j`<div class="message">${bt(t,"empty")}</div>`;const e=this._data.filter(t=>"electricity"===t.supply),i=e.length>1;return j`
      ${e.map(e=>j`
          <div class="section">
            ${i?j`<h3 class="chart-name">${e.name}</h3>`:V}
            <curenergia-bar-chart
              .hass=${t}
              .invoices=${e.invoices}
            ></curenergia-bar-chart>
          </div>
        `)}
      <div class="section">
        <curenergia-invoice-table
          .hass=${t}
          .contracts=${this._data}
          .supply=${this._supply}
          @supply-changed=${this._onSupplyChanged}
        ></curenergia-invoice-table>
      </div>
    `}render(){const t=this._hass;if(!t)return V;const e=this._summary;return j`
      <div class="toolbar">
        <ha-menu-button .hass=${t} .narrow=${this.narrow}></ha-menu-button>
        <div class="title">${bt(t,"panel_title")}</div>
      </div>
      <div class="content">
        ${this._failed?j`<div class="message error">${bt(t,"error")}</div>`:V}
        ${this._renderKpis(t)}
        ${e?.mail_error?j`<div class="warning">${bt(t,"panel_mail_error")}</div>`:V}
        ${e&&e.unreadable_emails>0?j`<div class="warning">
              ${bt(t,"panel_unreadable",{n:e.unreadable_emails})}
            </div>`:V}
        ${e&&e.unsupported_emails>0?j`<div class="warning">
              ${bt(t,"panel_unsupported",{n:e.unsupported_emails})}
            </div>`:V}
        ${this._renderBody(t)}
      </div>
    `}}Wt.properties={hass:{attribute:!1},narrow:{type:Boolean},panel:{attribute:!1},_data:{state:!0},_summary:{state:!0},_failed:{state:!0},_supply:{state:!0}},Wt.styles=a`
    :host {
      display: block;
      min-height: 100%;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 8px;
      height: 56px;
      padding: 0 12px;
      box-sizing: border-box;
      background: var(--app-header-background-color);
      color: var(--app-header-text-color, var(--primary-text-color));
    }
    .toolbar .title {
      font-size: 20px;
      font-weight: 400;
    }
    .content {
      max-width: 1100px;
      margin: 0 auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .kpis {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }
    .kpi,
    .section {
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 16px;
    }
    .kpi .value {
      font-size: 1.8em;
      font-weight: 500;
    }
    .kpi .label {
      margin-top: 4px;
      color: var(--secondary-text-color);
    }
    .warning {
      padding: 8px 12px;
      border-left: 4px solid var(--warning-color);
      background: var(--card-background-color);
      border-radius: 4px;
    }
    .chart-name {
      color: var(--secondary-text-color);
      font-size: 1em;
      font-weight: 500;
      margin: 0 0 4px;
    }
    .message {
      padding: 8px 0;
      color: var(--secondary-text-color);
    }
    .message.error {
      color: var(--error-color);
    }
  `,customElements.get("curenergia-panel")||customElements.define("curenergia-panel",Wt);
